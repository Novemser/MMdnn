import sys as _sys
import google.protobuf.text_format as text_format
from six import text_type as _text_type


def _convert(args):
    if args.srcFramework == 'caffe':
        from mmdnn.conversion.caffe.transformer import CaffeTransformer
        transformer = CaffeTransformer(args.network, args.weights, "tensorflow", args.inputShape, phase = args.caffePhase)
        graph = transformer.transform_graph()
        data = transformer.transform_data()

        from mmdnn.conversion.caffe.writer import JsonFormatter, ModelSaver, PyWriter
        JsonFormatter(graph).dump(args.dstPath + ".json")
        print ("IR network structure is saved as [{}.json].".format(args.dstPath))

        prototxt = graph.as_graph_def().SerializeToString()
        with open(args.dstPath + ".pb", 'wb') as of:
            of.write(prototxt)
        print ("IR network structure is saved as [{}.pb].".format(args.dstPath))
        
        import numpy as np
        with open(args.dstPath + ".npy", 'wb') as of:
            np.save(of, data)
        print ("IR weights are saved as [{}.npy].".format(args.dstPath))
        
        return 0

    elif args.srcFramework == 'caffe2':
        raise NotImplementedError("Caffe2 is not supported yet.")

    elif args.srcFramework == 'keras':
        if args.network != None:
            model = (args.network, args.weights)
        else:
            model = args.weights

        from mmdnn.conversion.keras.keras2_parser import Keras2Parser
        parser = Keras2Parser(model)

    elif args.srcFramework == 'tensorflow' or args.srcFramework == 'tf':
        if args.dstNodeName is None:
            raise ValueError("Need to provide the output node of Tensorflow model.")

        assert args.network or args.frozen_pb

        from mmdnn.conversion.tensorflow.tensorflow_parser import TensorflowParser
        parser = TensorflowParser(args.network, args.weights, args.frozen_pb, args.dstNodeName)

    elif args.srcFramework == 'mxnet':
        assert args.inputShape != None
        if args.weights == None:
            model = (args.network, args.inputShape)
        else:
            import re
            if re.search('.', args.weights):
                args.weights = args.weights[:-7]
            prefix, epoch = args.weights.rsplit('-', 1)
            model = (args.network, prefix, epoch, args.inputShape)

        from mmdnn.conversion.mxnet.mxnet_parser import MXNetParser
        parser = MXNetParser(model)

    elif args.srcFramework == 'cntk':
        from mmdnn.conversion.cntk.cntk_parser import CntkParser
        model = args.network or args.weights
        parser = CntkParser(model)

    elif args.srcFramework == 'pytorch':
        from mmdnn.conversion.pytorch.pytorch_parser import PyTorchParser
        model = args.network
        parser = PyTorchParser(model, 2)

    else:
        raise ValueError("Unknown framework [{}].".format(args.srcFramework))

    parser.run(args.dstPath)

    return 0


def _main():
    import argparse

    parser = argparse.ArgumentParser(description = 'Convert other model file formats to IR format.')
    
    parser.add_argument(
        '--srcFramework', '-f',
        type=_text_type,
        choices=["caffe", "caffe2", "cntk", "mxnet", "keras", "tensorflow", 'tf', 'pytorch'],
        help="Source toolkit name of the model to be converted.")

    parser.add_argument(
        '--weights', '-w', '-iw',
        type=_text_type,
        default=None,
        help='Path to the model weights file of the external tool (e.g caffe weights proto binary, keras h5 binary')

    parser.add_argument(
        '--network', '-n', '-in',
        type=_text_type,
        default=None,
        help='Path to the model network file of the external tool (e.g caffe prototxt, keras json')

    parser.add_argument(
        '--dstPath', '-d', '-o',
        type=_text_type,
        required=True,
        help='Path to save the IR model.')

    parser.add_argument(
        '--dstNodeName', '-node',
        type=_text_type,
        default=None,
        help="[Tensorflow] Output nodes' name of the graph.")

    parser.add_argument(
        '--frozen_pb',
        type=_text_type,
        default=None,
        help="[Tensorflow] frozen model file.")


    parser.add_argument(
        '--inputShape',
        nargs='+',
        type=int,
        default=None,
        help='[MXNet/Caffe2/PyTorch] Input shape of model (channel, height, width)')


    # Caffe
    parser.add_argument(
        '--caffePhase',
        type=_text_type,
        default='TRAIN',
        help='[Caffe] Convert the specific phase of caffe model.')

    args = parser.parse_args()
    ret = _convert(args)
    _sys.exit(int(ret)) # cast to int or else the exit code is always 1


if __name__ == '__main__':
    _main()
