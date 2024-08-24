import os
import json
from typing import Dict, Any
from datasets import load_dataset
from PIL import Image
import io
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def load_hugging_face_image(item, column: str) -> Image.Image:
    image = item[column]

    if isinstance(image, dict) and 'bytes' in image:
        return Image.open(io.BytesIO(image['bytes']))
    elif isinstance(image, Image.Image):
        return image
    elif isinstance(image, str):
        return Image.open(image)
    else:
        raise ValueError(f"Unknown image format: {type(image)}")


def create_json_entry(dataset, dataset_name: str, item, id: int, mapping: Dict[str, str]) -> Dict[str, Any]:
    entry = {
        "id": f"{dataset_name}-{id}",
        "type": "image",
        "hash": "tbd",
        "phash": "tbd",
        "urls": [],
        "status": "available",
        "flags": 0,
        "meta": {
            "hf-dataset-name": dataset_name,
            "hf-dataset-id": id
        },
        "fromUser": None,
        "fromTeam": None,
        "embeddings": [],
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "name": None,
        "width": None,
        "height": None,
        "format": None,
        "license": None,
        "licenseUrl": None,
        "contentAuthor": None
    }

    for target_field, source_field in mapping.items():
        if source_field and source_field in dataset.features:
            if target_field == 'image':
                image = load_hugging_face_image(item, source_field)
                entry['width'] = image.width
                entry['height'] = image.height
                entry['format'] = image.format.lower() if image.format else 'unknown'
            elif target_field == 'annotation':
                entry['annotations'] = [{
                    "id": f"{entry['id']}-annotation-1",
                    "content": entry['id'],
                    "annotation": {
                        "type": "image-description",
                        "text": item[source_field],
                        "tags": []
                    },
                    "manuallyAdjusted": False,
                    "embedding": None,
                    "fromUser": None,
                    "fromTeam": None,
                    "createdAt": entry['createdAt'],
                    "updatedAt": entry['updatedAt'],
                    "overallRating": None
                }]
            elif target_field == 'url':
                entry['urls'] = [item[source_field]]
            else:
                entry[target_field] = item[source_field]

    return entry


def convert_dataset_to_json(dataset_name: str, mapping_file: str, output_dir: str, num_samples: int = 10):
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)['field_mapping']

    dataset = load_dataset(dataset_name, split='train', streaming=True)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, item in enumerate(dataset.take(num_samples)):
        json_entry = create_json_entry(dataset, dataset_name, item, i, mapping)
        output_file = os.path.join(output_dir, f"{json_entry['id']}.json")
        with open(output_file, 'w') as f:
            json.dump(json_entry, f, indent=2, cls=DateTimeEncoder)
            f.write('\n')

    print(f"Created {num_samples} JSON files in {output_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python script.py <dataset_name> <mapping_file> <output_dir>")
        sys.exit(1)

    dataset_name = sys.argv[1]
    mapping_file = sys.argv[2]
    output_dir = sys.argv[3]

    convert_dataset_to_json(dataset_name, mapping_file, output_dir)
