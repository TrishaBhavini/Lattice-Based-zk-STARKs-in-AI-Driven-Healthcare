# Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare

## Dataset and Model
The dataset and CNN model used in this project are based on the following GitHub repository:  
[https://github.com/rishavchanda/Brain-Tumor-Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)

## How to Execute

Follow the steps below to set up and run the pipeline.

### 1. Clone the Repository
```bash
git clone https://github.com/TrishaBhavini/Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare.git
cd Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare
````

Ensure your repository contains the following files:

```
zkp-1.py
requirements.txt
```

---

### 2. Download the Pre-trained Model and Dataset

Download the model files and dataset from the following GitHub repository:
🔗 **Source:** [rishavchanda/Brain-Tumor-Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)

#### Required Files:

* `model.json`
* `model.h5`
* `datasets/` folder (contains brain MRI images)

After downloading, place them in the same directory as your script:

```
/project-folder
 ├── zkp-1.py
 ├── requirements.txt
 ├── model.json
 ├── model.h5
 └── dataset/
```

---

### 3. Install Dependencies

Make sure you have **Python 3.9+** installed. Then, install the required libraries:

```bash
pip install -r requirements.txt
```

This installs all necessary packages such as:

* TensorFlow & Keras
* NumPy, Pandas, Matplotlib
* OpenCV & Pillow

---

### 4. Run the ZKP Pipeline

Execute the following command to start the pipeline:

```bash
python3 zkp-1.py --dataset Brain-Tumor-Data --model_json model.json --model_h5 model.h5 
```

#### Arguments:

| Argument       | Description                                   | Default   |
| -------------- | --------------------------------------------- | --------- |
| `--dataset`    | Path to dataset folder                        | —         |
| `--model_json` | Path to model architecture file               | —         |
| `--model_h5`   | Path to model weights file                    | —         |

---

### 5. Output Files & Results

After execution, the following files will be generated in your working directory:

| File Name                       | Description                                                   |
| ------------------------------- | ------------------------------------------------------------- |
| `seq_results_<size>x<size>.csv` | Sequential proof and verification results for each image size |
| `batch_results_per_size.csv`    | Batch proof generation and verification timings               |
| `sequential_totals.png`         | Plot of total proof/verify time vs image size                 |
| `batch_times.png`               | Plot of proof/verify times across batch sizes                 |

---

### 6. Verify Output

* The console displays logs for each image (positive/negative cases).
* Proofs are generated and verified automatically.
* Plots visualize the efficiency of **Sequential** vs **Batch** proof generation.

Example console output:

```
✅ Model loaded successfully
[8] Y1.jpg run0: positive -> gen=0.0342s ver=0.0019s ok=True
[8] Y2.jpg run0: negative -> skipped
[Batch size 3 @ 8x8] gen=0.0783s ver=0.0024s ok=True
Saved sequential_totals.png
Saved batch_times.png
```

### Reference

Model & dataset source:
[Rishav Chanda – Brain Tumor Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)
