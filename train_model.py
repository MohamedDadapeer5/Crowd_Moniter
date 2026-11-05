import os
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import tensorflow_hub as hub
import PIL
from PIL.ImageDraw import Draw
import time
import concurrent.futures
from tqdm import tqdm

# ===================== CONFIG =====================
# Default dataset paths (absolute paths provided)
DATASET_PATH = r'D:\RVU\projects\crowd_detection_project\images.npy'  # Local dataset path
META_FILE = r'D:\RVU\projects\crowd_detection_project\labels.csv'     # CSV with image IDs and counts
FRAME_DIR = r'D:\RVU\projects\crowd_detection_project\frames'         # Directory containing frame images

AUTOTUNE = tf.data.experimental.AUTOTUNE
EPOCHS = 100
BATCH_SIZE = 16
PATIENCE = 10
LEARNING_RATE = 1e-3
IMAGE_SIZE = 299

# ===================== UTILITY FUNCTIONS =====================
def reconstruct_path(image_id: int) -> str:
    """Build path to a frame image using local paths."""
    image_id = str(image_id).rjust(6, '0')
    return os.path.join(FRAME_DIR, f'seq_{image_id}.jpg')

def detect_objects(path: str, model) -> dict:
    """Run object detection model on image."""
    image_tensor = tf.image.decode_jpeg(tf.io.read_file(path), channels=3)[tf.newaxis, ...]
    return model(image_tensor)

def count_persons(path: str, model, threshold=0.) -> int:
    """Count number of persons in an image."""
    results = detect_objects(path, model)
    return (results['detection_classes'].numpy()[0] == 1)[
        np.where(results['detection_scores'].numpy()[0] > threshold)
    ].sum()

def draw_bboxes(image_path, data: dict, threshold=0.3) -> PIL.Image.Image:
    """Draw bounding boxes around detected persons."""
    image = PIL.Image.open(image_path).convert("RGB")
    draw = Draw(image)
    im_width, im_height = image.size

    boxes = data['detection_boxes'].numpy()[0]
    classes = data['detection_classes'].numpy()[0].astype(int)
    scores = data['detection_scores'].numpy()[0]

    for i in range(int(data['num_detections'][0])):
        if classes[i] == 1 and scores[i] > threshold:
            ymin, xmin, ymax, xmax = boxes[i]
            top, left, bottom, right = (ymin * im_height, xmin * im_width, ymax * im_height, xmax * im_width)
            draw.rectangle([(left, top), (right, bottom)], outline='red', width=4)
            draw.text((left, top), f"{scores[i]:.2f}", fill="yellow")
    return image

def set_display():
    """Set display options for plots and DataFrames."""
    plt.style.use('fivethirtyeight')
    plt.rcParams['figure.figsize'] = 12, 8
    plt.rcParams.update({'font.size': 14})
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.options.display.float_format = '{:.4f}'.format

set_display()

# ===================== LOAD DATA =====================
images = np.load(DATASET_PATH)
print("Dataset shape:", images.shape)

try:
    data = pd.read_csv(META_FILE)
except UnicodeDecodeError:
    data = pd.read_csv(META_FILE, encoding='latin1')
print("✅ CSV loaded successfully!")
data['path'] = data['id'].apply(reconstruct_path)
print(data.head())

# Visualize target distribution
stats = data.describe()
plt.hist(data['count'], bins=20)
plt.axvline(stats.loc['mean', 'count'], label='Mean value', color='green')
plt.legend()
plt.xlabel('Number of people')
plt.ylabel('Frequency')
plt.title('Target Values')
plt.show()

# ===================== OBJECT DETECTION =====================
MODEL_PATH = "https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2"
detector = hub.load(MODEL_PATH)
print("SSD MobileNet V2 model loaded successfully!")

# Example detection
example_path = data['path'].iloc[0]
results = detect_objects(example_path, detector)
draw_bboxes(example_path, results, threshold=0.25)

# ===================== SAMPLE PREDICTIONS =====================
sample = data.sample(frac=0.1)
start = time.perf_counter()
objects = []

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(count_persons, path, detector, 0.25) for path in sample['path']]
    for f in tqdm(concurrent.futures.as_completed(futures)):
        objects.append(f.result())

finish = time.perf_counter()
print(f'Finished in {round(finish - start, 2)} second(s).')

sample['prediction'] = objects
sample['mae'] = (sample['count'] - sample['prediction']).abs()
sample['mse'] = sample['mae'] ** 2
print(f"MAE = {sample['mae'].mean():.4f}\nMSE = {sample['mse'].mean():.4f}")

plt.hist(sample['mae'], bins=20)
plt.title('Absolute Errors')
plt.show()

plt.scatter(sample['count'], sample['prediction'])
plt.xlabel('Actual person count')
plt.ylabel('Predicted person count')
plt.title('Predicted vs. Actual Count')
plt.show()

# ===================== TRAINING DATA PREP =====================
def load_image(is_labelled: bool, is_training=True):
    """Returns a function that loads and preprocesses a single image."""
    def _get_image(path: str) -> tf.Tensor:
        image = tf.image.decode_jpeg(tf.io.read_file(path), channels=3)
        image = tf.cast(image, dtype=tf.float32)
        image = tf.image.resize_with_pad(image, IMAGE_SIZE, IMAGE_SIZE)
        if is_training:
            image = tf.image.random_flip_left_right(image)
            image = tf.image.random_brightness(image, 0.1)
            image = tf.image.random_contrast(image, 0.9, 1.1)
            image = tf.image.random_saturation(image, 0.9, 1.1)
            image = tf.image.random_hue(image, 0.05)
        return tf.keras.applications.inception_resnet_v2.preprocess_input(image)

    def _get_image_label(img: tf.Tensor, label: int) -> tuple:
        return _get_image(img), label

    return _get_image_label if is_labelled else _get_image

def prepare_dataset(dataset, is_training=True, is_labeled=True):
    image_read_fn = load_image(is_labeled, is_training)
    dataset = dataset.map(image_read_fn, num_parallel_calls=AUTOTUNE)
    if is_training:
        dataset = dataset.shuffle(1000)
    return dataset.batch(BATCH_SIZE).prefetch(AUTOTUNE)

def create_model() -> tf.keras.Model:
    """Regression model with pretrained InceptionResNetV2."""
    base_model = tf.keras.applications.InceptionResNetV2(
        include_top=False, pooling='avg', input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3)
    )
    base_model.trainable = False

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.Dense(512, activation='selu'),
        tf.keras.layers.Dense(1)
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=tf.keras.losses.MeanSquaredError(),
        metrics=[tf.keras.metrics.MeanAbsoluteError()]
    )
    return model

def plot_history(hist):
    mae = hist.history['mean_absolute_error']
    val_mae = hist.history['val_mean_absolute_error']
    x_axis = range(1, len(mae) + 1)
    plt.plot(x_axis, mae, 'bo', label='Training MAE')
    plt.plot(x_axis, val_mae, 'ro', label='Validation MAE')
    plt.title('Mean Absolute Error (MAE)')
    plt.legend()
    plt.xlabel('Epochs')
    plt.tight_layout()
    plt.show()

def set_seed(seed=42):
    np.random.seed(seed)
    random.seed(seed)
    tf.random.set_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'

set_seed()

# Split data
data_train = data.head(1700)
data_valid = data.tail(300)

ds_train = tf.data.Dataset.from_tensor_slices((data_train['path'], data_train['count']))
ds_valid = tf.data.Dataset.from_tensor_slices((data_valid['path'], data_valid['count']))

ds_train = prepare_dataset(ds_train)
ds_valid = prepare_dataset(ds_valid, is_training=False)

model = create_model()

early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=PATIENCE, restore_best_weights=True)
lr_reduction = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', patience=1, cooldown=1, verbose=1,
                                                    factor=0.75, min_lr=1e-8)

history = model.fit(ds_train, validation_data=ds_valid, epochs=EPOCHS, callbacks=[early_stop, lr_reduction])
plot_history(history)

mse, mae = model.evaluate(ds_valid)
print(f'Validation MSE = {mse}\nValidation MAE = {mae}')

model.save('model.h5')
print("✅ Model saved as model.h5")
