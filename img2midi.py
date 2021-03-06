from PIL import Image
import numpy as np
from music21 import instrument, note, chord, stream
import sys
from pathlib import Path

lowerBoundNote = 21
def column2notes(column):
    notes = []
    for i in range(len(column)):
        if column[i] > 255/2:
            notes.append(i+lowerBoundNote)
    return notes

resolution = 0.25
def updateNotes(newNotes,prevNotes): 
    res = {} 
    for note in newNotes:
        if note in prevNotes:
            res[note] = prevNotes[note] + resolution
        else:
            res[note] = resolution
    return res

class Img2Midi:
    def __init__(self, image_path):
        self.image_path = image_path
        self.im_arr = None
        self.read_image()

    def read_image(self):
        with Image.open(self.image_path) as image:
            self.im_arr = np.fromstring(image.tobytes(), dtype=np.uint8)
            try:
                self.im_arr = self.im_arr.reshape((image.size[1], image.size[0]))
            except:
                self.im_arr = self.im_arr.reshape((image.size[1], image.size[0],3))
                self.im_arr = np.dot(im_arr, [0.33, 0.33, 0.33])
            print(self.im_arr.shape)

    def image2midi(self, outdir = "output_midi"):
        """ convert the output from the prediction to notes and create a midi file
            from the notes """
        offset = 0
        output_notes = []

        # create note and chord objects based on the values generated by the model

        prev_notes = updateNotes(self.im_arr.T[0,:],{})
        for column in self.im_arr.T[1:,:]:
            notes = column2notes(column)
            # pattern is a chord
            notes_in_chord = notes
            old_notes = prev_notes.keys()
            for old_note in old_notes:
                if not old_note in notes_in_chord:
                    new_note = note.Note(old_note,quarterLength=prev_notes[old_note])
                    new_note.storedInstrument = instrument.Piano()
                    if offset - prev_notes[old_note] >= 0:
                        new_note.offset = offset - prev_notes[old_note]
                        output_notes.append(new_note)
                    elif offset == 0:
                        new_note.offset = offset
                        output_notes.append(new_note)                    
                    else:
                        print(offset,prev_notes[old_note],old_note)

            prev_notes = updateNotes(notes_in_chord,prev_notes)

            # increase offset each iteration so that notes do not stack
            offset += resolution

        for old_note in prev_notes.keys():
            new_note = note.Note(old_note,quarterLength=prev_notes[old_note])
            new_note.storedInstrument = instrument.Piano()
            new_note.offset = offset - prev_notes[old_note]

            output_notes.append(new_note)

        prev_notes = updateNotes(notes_in_chord,prev_notes)

        midi_stream = stream.Stream(output_notes)
        Path(outdir).mkdir(parents=True, exist_ok=True)
        out_path = outdir + "/" + self.image_path.split("/")[-1].replace(".png",".mid")
        midi_stream.write('midi', fp=out_path)
        return out_path

# image_path = sys.argv[1]
# image2midi(image_path)

