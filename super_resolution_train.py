import random
import glob
import subprocess
import os
from PIL import Image
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras import layers
from tensorflow.keras import backend as K

# automatically get the data if it doesn't exist
if not os.path.exists("data"):
    print("Downloading flower dataset...")
    subprocess.check_output(
        "mkdir data && curl https://storage.googleapis.com/wandb/flower-enhance.tar.gz | tar xzf - -C data", shell=True)

class SUPER_RESOLUTION_PIXELS():
    def __init__(self):
        self.num_epochs = 20
        self.batch_size = 32
        self.input_height = 32
        self.input_width = 32
        self.output_height = 256
        self.output_width = 256
        self.val_dir = 'data/test'
        self.train_dir = 'data/train'

        self.num_steps_per_epoch = len(
            glob.glob(self.train_dir + "/*-in.jpg")) // self.batch_size
        self.val_steps_per_epoch = len(
            glob.glob(self.val_dir + "/*-in.jpg")) // self.batch_size

        self.val_generator = self.image_generator(self.batch_size, self.val_dir)
        self.in_sample_images, self.out_sample_images = next(self.val_generator)

    def build_model(self):
        self.model = Sequential()
        self.model.add(layers.Conv2D(3, (3, 3), activation='relu', padding='same',
                                input_shape=(self.input_width, self.input_height, 3)))
        self.model.add(layers.UpSampling2D())
        self.model.add(layers.Conv2D(3, (3, 3), activation='relu', padding='same'))
        self.model.add(layers.UpSampling2D())
        self.model.add(layers.Conv2D(3, (3, 3), activation='relu', padding='same'))
        self.model.add(layers.UpSampling2D())
        self.model.add(layers.Conv2D(3, (3, 3), activation='relu', padding='same'))

        # DONT ALTER metrics=[perceptual_distance]
        self.model.compile(optimizer='adam', loss='mse',
                      metrics=[self.perceptual_distance])

    def train(self):
        self.model.fit_generator(self.image_generator(self.batch_size, self.train_dir),
                            steps_per_epoch=self.num_steps_per_epoch,
                            epochs=self.num_epochs,
                            validation_steps=self.val_steps_per_epoch,
                            validation_data=self.val_generator)

        self.model.save('sres_model.h5')

    def image_generator(self, nbatch_size, img_dir):
        """A generator that returns small images and large images.  DO NOT ALTER the validation set"""
        input_filenames = glob.glob(img_dir + "/*-in.jpg")
        counter = 0
        random.shuffle(input_filenames)
        while True:
            small_images = np.zeros(
                (nbatch_size, self.input_width, self.input_height, 3))
            large_images = np.zeros(
                (nbatch_size, self.output_width, self.output_height, 3))
            if counter+nbatch_size >= len(input_filenames):
                counter = 0
            for i in range(nbatch_size):
                img = input_filenames[counter + i]
                small_images[i] = np.array(Image.open(img)) / 255.0
                large_images[i] = np.array(
                    Image.open(img.replace("-in.jpg", "-out.jpg"))) / 255.0
            yield (small_images, large_images)
            counter += nbatch_size

    def perceptual_distance(self, y_true, y_pred):
        """Calculate perceptual distance, DO NOT ALTER"""
        y_true *= 255
        y_pred *= 255
        rmean = (y_true[:, :, :, 0] + y_pred[:, :, :, 0]) / 2
        r = y_true[:, :, :, 0] - y_pred[:, :, :, 0]
        g = y_true[:, :, :, 1] - y_pred[:, :, :, 1]
        b = y_true[:, :, :, 2] - y_pred[:, :, :, 2]

        return K.mean(K.sqrt((((512+rmean)*r*r)/256) + 4*g*g + (((767-rmean)*b*b)/256)))


def main():
    sr_pixels = SUPER_RESOLUTION_PIXELS()
    sr_pixels.build_model()
    sr_pixels.train()

if __name__ == "__main__":
    main()
