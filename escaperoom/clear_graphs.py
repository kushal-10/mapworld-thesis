import os
import glob
import shutil


def delete_graph_folders(root_dir='.'):
    """
    Deletes all directories named 'graphs' under the given root directory.

    This will remove:
      - escaperoom/graphs
      - results/*/escape_room/*/episode_*/graphs
      - any other 'graphs' folders recursively found under root_dir

    :param root_dir: Path to the repository root or base directory to search in.
    """
    # Use glob to find all 'graphs' directories recursively
    pattern = os.path.join(root_dir, '**', 'combined_graphs')
    dirs = glob.glob(pattern, recursive=True)

    if not dirs:
        print("No 'graphs' folders found to delete.")
        return

    for d in dirs:
        if os.path.isdir(d):
            try:
                shutil.rmtree(d)
                print(f"Deleted folder: {d}")
            except Exception as e:
                print(f"Failed to delete {d}: {e}")


def main():
    # Change '.' to another path if needed
    delete_graph_folders('.')

if __name__ == '__main__':
    main()
