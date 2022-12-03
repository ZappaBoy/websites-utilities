import argparse
import os

import imagehash
from PIL import Image
from html_similarity import style_similarity, structural_similarity, similarity

local_dir = os.path.dirname(__file__)
generated_resources_dir = os.path.join(local_dir, 'generated_resources')
os.makedirs(generated_resources_dir, exist_ok=True)


class SnapshotDiff:

    def __init__(self, original_snapshot_dir, modified_snapshot_dir):
        self.original_snapshot_dir = original_snapshot_dir
        self.modified_snapshot_dir = modified_snapshot_dir

    @staticmethod
    def get_html_content_dir(snapshot_path) -> str:
        return os.path.join(snapshot_path, 'html_content')

    @staticmethod
    def get_screenshot_dir(snapshot_path) -> str:
        return os.path.join(snapshot_path, 'screenshots')

    def get_html_content_differences(self) -> float:
        total_score = 0.0
        differences = 0.0

        original_html_content_dir = self.get_html_content_dir(self.original_snapshot_dir)
        modified_html_content_dir = self.get_html_content_dir(self.modified_snapshot_dir)
        original_html_content_files = sorted(os.listdir(original_html_content_dir))
        modified_html_content_files = sorted(os.listdir(modified_html_content_dir))

        j = 0
        for original_html in original_html_content_files:

            if len(modified_html_content_files) <= j:
                print(f'File {original_html} not found in modified snapshot')
                continue
            modified_html = modified_html_content_files[j]
            print(f'> Comparing {original_html} and {modified_html}')
            if original_html != modified_html:
                print(f'File {original_html} not found in modified snapshot')
                continue
            else:
                j += 1

            original_html_content_file = os.path.join(original_html_content_dir, original_html)
            modified_html_content_file = os.path.join(modified_html_content_dir, modified_html)
            with open(original_html_content_file, 'r') as f:
                original_html_content = f.read()
            with open(modified_html_content_file, 'r') as f:
                modified_html_content = f.read()

            structural_similarity_value = structural_similarity(original_html_content, modified_html_content)
            style_similarity_value = style_similarity(original_html_content, modified_html_content)
            similarity_value = similarity(original_html_content, modified_html_content)

            print(f'Structural similarity: {structural_similarity_value}')
            print(f'Style similarity: {style_similarity_value}')
            print(f'Similarity: {similarity_value}')

            total_score += 3
            differences += 3 - (structural_similarity_value + style_similarity_value + similarity_value)

        score = (total_score - differences) / total_score * 100
        if differences == 0:
            print('No differences found')
        else:
            print(f'Similarity: {score}%')

        return score

    def get_screenshots_differences(self) -> float:
        total_score = 0.0
        differences = 0.0

        original_screenshot_dir = self.get_screenshot_dir(self.original_snapshot_dir)
        modified_screenshot_dir = self.get_screenshot_dir(self.modified_snapshot_dir)
        original_screenshot_files = sorted(os.listdir(original_screenshot_dir))
        modified_screenshot_files = sorted(os.listdir(modified_screenshot_dir))

        j = 0
        for original_screenshot in original_screenshot_files:
            if len(modified_screenshot_files) <= j:
                print(f'File {original_screenshot} not found in modified snapshot')
                continue
            modified_screenshot = modified_screenshot_files[j]
            print(f'> Comparing {original_screenshot} and {modified_screenshot}')
            if original_screenshot != modified_screenshot:
                print(f'File {original_screenshot} not found in modified snapshot')
                continue
            else:
                j += 1

            original_screenshot_file = os.path.join(original_screenshot_dir, original_screenshot)
            modified_screenshot_file = os.path.join(modified_screenshot_dir, modified_screenshot)

            original_screenshot = Image.open(original_screenshot_file)
            modified_screenshot = Image.open(modified_screenshot_file)

            original_hash = imagehash.average_hash(original_screenshot)
            modified_hash = imagehash.average_hash(modified_screenshot)

            hashes_difference = original_hash - modified_hash

            cutoff = 5
            if hashes_difference < cutoff:
                print('images are similar')
            else:
                print('images are not similar')

            total_score += 64  # 64 bits hashes - 8x8 monochrome thumbnail
            differences += hashes_difference

        score = (total_score - differences) / total_score * 100
        if differences == 0:
            print('No differences found')
        else:
            print(f'Similarity: {(total_score - differences) / total_score * 100}%')

        return score

    def check_snapshots_differences(self) -> None:
        html_score = self.get_html_content_differences()
        screenshots_score = self.get_screenshots_differences()
        print(f'Overall similarity: {(html_score + screenshots_score) / 2}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create snapshot for a website')
    parser.add_argument('--original', '-o', type=str, help='The path of the original/first snapshot', default=None)
    parser.add_argument('--modified', '-m', type=str, help='The path of the modified/second snapshot', default=None)
    args = parser.parse_args()

    snapshot_diff = SnapshotDiff(args.original, args.modified)
    snapshot_diff.check_snapshots_differences()
