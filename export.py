import torch
from facenet_pytorch import MTCNN

mtcnn = MTCNN()
torch.save(mtcnn, 'mtcnn.pth')
