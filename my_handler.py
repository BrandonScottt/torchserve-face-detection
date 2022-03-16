from face_detection import face_detection
from ts.torch_handler.base_handler import BaseHandler

_service = face_detection()


def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)

    if data is None:
        return None
    
    model_input, path = _service.preprocess(data)
    model_output = _service.inference(model_input)
    images = _service.postprocess(model_output, model_input, path)
    data = _service.saveImage(images, path)
    return data

# if __name__ == "__main__":
#     data = 'img1.jpg'

#     test = face_detection()

#     model_input, path = test.preprocess(data)
#     model_output = test.inference(model_input)
#     images = test.postprocess(model_output, model_input, path)
#     out = test.saveImage(images, path)