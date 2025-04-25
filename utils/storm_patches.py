import logging
import os
logger = logging.getLogger("storm_patch")


def apply_patches():
    """
    Apply simple patches to the STORM library.
    Returns:
        bool: True if patching was successful, False otherwise
    """

    try:
        import storm
        logger.info(f"STORM library found")
    except ImportError:
        logger.critical(
            "STORM library not found! Please clone the STORM repository:\n"
            "git clone https://github.com/stanford-oval/storm.git"
        )
        return False

    try:
        from storm.knowledge_storm import utils

        if hasattr(utils, 'FileIOHelper'):
            original_write_str = utils.FileIOHelper.write_str
            @staticmethod
            def enhanced_write_str(s, path):
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(s)

            utils.FileIOHelper.write_str = enhanced_write_str


        else:
            logger.error("Failed to patch STORM: FileIOHelper class not found in utils module")
            return False

    except Exception as e:
        logger.error(f"Failed to patch STORM: {e}")
        return False