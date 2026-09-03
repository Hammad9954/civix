from PIL import Image
import imagehash


def compare_images(
    before_path,
    after_path
):

    try:

        before = Image.open(
            before_path
        )

        after = Image.open(
            after_path
        )

        before_hash = imagehash.phash(
            before
        )

        after_hash = imagehash.phash(
            after
        )

        distance = (
            before_hash -
            after_hash
        )

        max_distance = (
            len(before_hash.hash) ** 2
        )

        similarity = 1 - (
            distance /
            max_distance
        )

        return round(
            max(
                0,
                min(1, similarity)
            ),
            3
        )

    except Exception:

        return 0.0


def verify_resolution(
    before_path,
    after_path
):

    similarity = compare_images(
        before_path,
        after_path
    )

    if similarity < 0.70:

        return {
            "verified": True,
            "similarity": similarity,
            "message":
                "Significant visual change detected."
        }

    return {
        "verified": False,
        "similarity": similarity,
        "message":
            "Images appear too similar. "
            "Manual verification required."
    }