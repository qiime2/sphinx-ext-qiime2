from pathlib import Path


def get_docname(node):
    root, doc_name = [Path(p) for p in Path(node.source).parts[-2:]]
    doc_name = Path(doc_name.stem)
    return root, doc_name


def get_ext(source):
    if source == "metadata" or source == "init_metadata":
        return "tsv"
    return "qza"
