import torch
from facenet_pytorch import InceptionResnetV1

def get_facenet_model(device='cpu'):
    """
    Initializes and returns the pretrained FaceNet model (InceptionResnetV1)
    trained on VGGFace2.
    """
    model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    return model
