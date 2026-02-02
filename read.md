IA-FINAL: CPU-Based Incremental Object Detection with Continuous Retraining and MLflow Tracking

Project Overview

IA-FINAL is an end-to-end object detection system designed to work entirely on CPU, focused on continuous (incremental) learning from new user-provided data.
The system uses transfer learning on a COCO-pretrained detector and supports automatic retraining only on newly added images, avoiding full retraining from scratch.

The project integrates:

A modular notebook-based ML pipeline

MLflow for experiment tracking and model registry

A backend API for inference and retraining

A frontend interface for prediction, visualization, annotation, and retraining control

The target object classes are:

person

car

airplane

Main Features

Object detection using Faster R-CNN (ResNet-50 FPN)

CPU-optimized training and inference

Incremental retraining with new labeled images only

MLflow experiment tracking and model registry

Visual prediction results with bounding boxes and confidence scores

Manual annotation and correction of new data (YOLO format)

Automatic model reload after retraining

Real-time training progress logs in the UI

Technology Stack
Machine Learning & Data

Python 3.12

PyTorch

Torchvision

COCO 2017 Dataset

Transfer Learning

Incremental / Continual Learning

Experiment Tracking

MLflow

Experiments

Metrics

Artifacts

Model Registry

SQLite backend (mlflow_new.db)

Backend

FastAPI

Uvicorn

nbconvert (for automated notebook execution)

Frontend

Angular (standalone architecture)

TypeScript

Tailwind CSS

HTML Canvas (bounding box visualization and annotation)