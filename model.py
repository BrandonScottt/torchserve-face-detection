import torch
from facenet_pytorch import MTCNN #pip install facenet-pytorch

mtcnn = MTCNN()
torch.save(mtcnn, 'mtcnn.pth')
