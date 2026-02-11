# Artificial Intelligence Prediction Project

## Authors

**Juan Álvarez**  
alvareseu@est.ups.edu.ec  

**Johnny Segarra**  
jsegarrao1@est.ups.edu.ec  

Universidad Politécnica Salesiana, Cuenca, Ecuador  

---

## Abstract

**Problem.**  
Object detection in real-world images requires models capable of identifying multiple objects per image while continuously improving as new data becomes available. Training modern detectors typically relies on GPU resources, which limits accessibility in local or resource-constrained environments.

**Proposed Solution.**  
This work proposes a CPU-oriented object detection pipeline based on transfer learning using Faster R-CNN with a ResNet-50 FPN backbone, combined with a continual (incremental) learning strategy. The system updates the model exclusively with newly labeled user data while preserving previously acquired knowledge through controlled validation-based promotion.

**Dataset.**  
The MS COCO 2017 dataset is filtered to three target classes:

- person  
- car  
- airplane  

Only images containing at least one of these classes are retained, and labels are remapped to an internal index compatible with the detector. Evaluation is performed on a fixed validation subset to ensure comparability between baseline and incremental phases.

**Quality Measures.**

The baseline model achieved:

| Metric              | Value |
|---------------------|-------|
| Precision (micro)   | 0.506 |
| Recall (micro)      | 0.722 |
| F1-score (micro)    | 0.595 |
| mAP@0.5 (approx.)   | 0.558 |

After incremental retraining using seven newly labeled images:

- Validation loss decreased from **0.6709** to **0.6455**
- Improvement achieved in a **CPU-only configuration**
- All experiments tracked using **MLflow**

**Future Work.**

- Full COCO-style mAP evaluation across multiple IoU thresholds  
- Improved class balancing strategies  
- Hard-negative mining  
- Advanced continual learning techniques to mitigate catastrophic forgetting  

**Reproducibility.**  
Full replication content available at:  
https://github.com/johnny567w/Artificial_Intelligence_Prediction_proyect

---

# Proposed Method

The system architecture integrates:

- Dataset reduction  
- CPU-based transfer learning  
- Continual learning loop  
- MLflow experiment tracking  
- Model versioning and automated promotion  

---

## Model and Transfer Learning

The base detection architecture is:

**Faster R-CNN with ResNet-50 FPN backbone (Torchvision)**

### Transfer Learning Strategy

- Initialize model with COCO-pretrained weights  
- Replace detection head to support **N + 1 classes** (background + 3 targets)  
- Freeze backbone during incremental retraining to reduce CPU cost  

---

## Proposed Method Parameters (CPU)

| Name | Description | Typical Value (CPU) |
|------|------------|---------------------|
| TARGET_CLASSES | Target object classes | person, car, airplane |
| model_arch | Detector architecture | Faster R-CNN ResNet50-FPN |
| image_size_cap | Max inference resolution | 960 (or 720) |
| score_threshold | Confidence threshold | 0.50 |
| batch_size | Training batch size | 1–2 |
| epochs_base | Baseline epochs | 1–3 |
| epochs_incr | Incremental epochs | 1–3 |
| train_backbone_incr | Train backbone incrementally | False |
| eval_max_images | Validation subset size | 20–200 |

---

# Key Algorithms

## Algorithm 1 — COCO Reduction to Target Classes

1. Load COCO annotations JSON  
2. Convert class names to COCO category IDs  
3. Filter annotations by target classes  
4. Retain images containing at least one valid annotation  
5. Save reduced dataset and class mapping  

---

## Algorithm 2 — Continual Learning Using Only New Images

1. Check for new labeled images  
2. If no new data → skip training and log status  
3. Load current production model  
4. Evaluate baseline validation loss  
5. Train on new data (few epochs)  
6. Re-evaluate validation loss  
7. If performance improves → register new version  
8. Log metrics and artifacts to MLflow  

---

# Experimental Design

## Dataset Characteristics

- Dataset: MS COCO 2017  
- Classes: person, car, airplane  
- Reduction: Only images with at least one target object  
- Continual data: User-labeled local images  

---

## Optimization Parameters

| Parameter | Baseline | Incremental |
|------------|----------|-------------|
| Optimizer | SGD / AdamW | Same |
| Learning Rate | Small | Smaller or equal |
| Epochs | 1–3 | 1–3 |
| Backbone | Optional | Frozen |
| Validation | Reduced subset | Same subset |

---

# Results and Discussion

## Baseline Evaluation

Evaluation performed on 300 validation images with:

- IoU ≥ 0.5  
- Confidence threshold = 0.5  

| Metric              | Value |
|---------------------|-------|
| Precision (micro)   | 0.506 |
| Recall (micro)      | 0.722 |
| F1-score (micro)    | 0.595 |
| mAP@0.5 (approx.)   | 0.558 |

### Class-wise AP@0.5

- person: 0.6368  
- car: 0.4877  
- airplane: 0.5500  

The model shows:

- High recall  
- Moderate precision  
- Car class affected by imbalance  

---

## Incremental Learning Impact

Incremental retraining:

- 7 new labeled images  
- 2 epochs  
- CPU mode  
- Backbone frozen  

### Validation Loss Comparison

| Metric | Baseline | After Incremental |
|--------|----------|-------------------|
| Validation Loss | 0.6709 | 0.6455 |
| Training Images (new) | 3000 | 7 |
| Epochs | 2 | 2 |
| Backbone Frozen | No | Yes |

Validation loss decreased by ~3.8%.

Model automatically promoted to production after satisfying improvement criteria.

---

# Discussion

The results demonstrate:

- CPU-only training is viable  
- Continual learning improves performance with very small datasets  
- Freezing backbone stabilizes updates  
- Class imbalance remains a limiting factor  
- MLflow ensures full reproducibility and traceability  

---

# Conclusions

This project presents a fully functional CPU-based object detection pipeline integrating:

- Transfer learning  
- Continual learning  
- Experiment tracking  
- Automated model promotion  

Baseline achieved:

- F1-score: 0.595  
- mAP@0.5: 0.558  

Incremental retraining reduced validation loss from:

0.6709 → 0.6455

Demonstrating measurable improvement without GPU acceleration.

Future work includes:

- Full COCO mAP evaluation  
- Better class balancing  
- Advanced incremental learning strategies  

---
