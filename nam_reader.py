import json
import numpy as np

class NAMReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.version = None
        self.architecture = None
        self.config = None
        self.weights = None
        self._load_nam_file()

    def _load_nam_file(self):
        """Load and parse a NAM file."""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.version = data.get('version')
                self.architecture = data.get('architecture')
                self.config = data.get('config')
                self.weights = np.array(data.get('weights', []))
        except Exception as e:
            raise Exception(f"Error loading NAM file: {str(e)}")

    def get_model_info(self):
        """Return basic information about the model."""
        return {
            'version': self.version,
            'architecture': self.architecture,
            'num_layers': len(self.config['layers']) if self.config and 'layers' in self.config else 0,
            'num_weights': len(self.weights) if self.weights is not None else 0
        }

    def get_layer_info(self, layer_idx=None):
        """Get information about specific layer or all layers."""
        if not self.config or 'layers' not in self.config:
            return None

        if layer_idx is not None:
            if 0 <= layer_idx < len(self.config['layers']):
                return self.config['layers'][layer_idx]
            return None

        return self.config['layers']

    def get_weights(self):
        """Return the model weights as numpy array."""
        return self.weights

def main():
    # Example usage
    nam_file = "Models/George B Ceriatone King Kong  chan2 60s br sw2 L.nam"
    try:
        reader = NAMReader(nam_file)
        model_info = reader.get_model_info()
        print("Model Information:")
        print(f"Version: {model_info['version']}")
        print(f"Architecture: {model_info['architecture']}")
        print(f"Number of layers: {model_info['num_layers']}")
        print(f"Number of weights: {model_info['num_weights']}")

        # Print first layer info
        layer_info = reader.get_layer_info(0)
        if layer_info:
            print("\nFirst Layer Configuration:")
            for key, value in layer_info.items():
                print(f"{key}: {value}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()