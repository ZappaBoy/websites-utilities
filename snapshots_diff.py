import argparse
import os
from html_similarity import style_similarity, structural_similarity, similarity


local_dir = os.path.dirname(__file__)
generated_resources_dir = os.path.join(local_dir, 'generated_resources')
os.makedirs(generated_resources_dir, exist_ok=True)


class SnapshotDiff:

    def __init__(self, original_snapshot, modified_snapshot):
        pass

    @staticmethod
    def get_pages_content_dir(snapshot_path):
        return os.path.join(snapshot_path, 'html_content')

    @staticmethod
    def get_screenshot_dir(snapshot_path):
        return os.path.join(snapshot_path, 'screenshots')

    def check_html_content_differences(self):
        # style_similarity(html_1, html_2)
        # structural_similarity(html_1, html_2)
        # similarity(html_1, html_2)
        pass

    def check_snapshots_differences(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create snapshot for a website')
    parser.add_argument('--original', '-o', type=str, help='The path of the original/first snapshot', default=None)
    parser.add_argument('--modified', '-m', type=str, help='The path of the modified/second snapshot', default=None)
    args = parser.parse_args()

    snapshot_diff = SnapshotDiff(args.original, args.modified)
    snapshot_diff.check_snapshots_differences()
    print('Done. Check the results in the generated_resources folder')
