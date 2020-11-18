from music21 import converter, instrument, note, chord
import json
import sys
import numpy as np
from imageio import imwrite
from pathlib import Path
from mido import MidiFile


def extractNote(element):
    return int(element.pitch.ps)

def extractDuration(element):
    return element.duration.quarterLength

def get_notes(notes_to_parse):

    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    durations = []
    notes = []
    start = []

    for element in notes_to_parse:
        if isinstance(element, note.Note):
            if element.isRest:
                continue

            start.append(element.offset)
            notes.append(extractNote(element))
            durations.append(extractDuration(element))
                
        elif isinstance(element, chord.Chord):
            if element.isRest:
                continue
            for chord_note in element.notes:
                start.append(element.offset)
                durations.append(extractDuration(element))
                notes.append(extractNote(chord_note))

    return {"start":start, "pitch":notes, "dur":durations}

class Midi2Img:
    def __init__(self, midi_path):
        self.midi_path = midi_path
        self.data = {}
        self.extract_data()
        self.length = self.get_length()
        self.im_list = []
    
    def get_length(self):
        m = MidiFile(self.midi_path)
        return m.length

    def instruments_list(self):
        return list(self.data.keys())

    def extract_data(self):
        self.mid = converter.parse(self.midi_path)
        instruments = instrument.partitionByInstrument(self.mid)

        try:
            i=0
            for instrument_i in instruments.parts:
                notes_to_parse = instrument_i.recurse()

                if instrument_i.partName is None:
                    self.data["instrument_{}".format(i)] = get_notes(notes_to_parse)
                    i+=1
                else:
                    self.data[instrument_i.partName] = get_notes(notes_to_parse)
        except:
            notes_to_parse = mid.flat.notes
            self.data["instrument_0".format(i)] = get_notes(notes_to_parse)

    def midi2image(self, outdir = "output", rep = 1): 
        resolution = 0.25
        im_list = []
        for instrument_name, values in self.data.items():
            # https://en.wikipedia.org/wiki/Scientific_pitch_notation#Similar_systems
            upperBoundNote = 127
            lowerBoundNote = 21
            maxSongLength = 720*2

            index = 0
            prev_index = 0
            repetitions = 0
            while repetitions < rep:
                if prev_index >= len(values["pitch"]):
                    break

                matrix = np.zeros((upperBoundNote-lowerBoundNote,maxSongLength))

                pitchs = values["pitch"]
                durs = values["dur"]
                starts = values["start"]

                for i in range(prev_index,len(pitchs)):
                    pitch = pitchs[i]

                    dur = int(durs[i]/resolution)
                    start = int(starts[i]/resolution)

                    if dur+start - index*maxSongLength < maxSongLength:
                        for j in range(start,start+dur):
                            if j - index*maxSongLength >= 0:
                                matrix[pitch-lowerBoundNote,j - index*maxSongLength] = 255
                    else:
                        prev_index = i
                        break

                matrix = (matrix * 255 / np.max(matrix)).astype('uint8')
                Path(outdir).mkdir(parents=True, exist_ok=True)
                imwrite(outdir + "/" + self.midi_path.split("/")[-1].replace(".mid",f"_{instrument_name}_{index}.png"),matrix)
                index += 1
                repetitions+=1
                im_list.append(matrix)
        self.im_list = im_list
        return im_list

# midi_path = sys.argv[1]
# rep = intsys.argv[2])
# midi2image(midi_path, rep)