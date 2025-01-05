from openpyxl.styles.colors import RGB, WHITE

if "custom" not in globals():
    from mage_ai.data_preparation.decorators import custom
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@custom
def transform_custom(*args, **kwargs):
    """Fix: 'ValueError: Colors must be aRGB hex values'
    From https://stackoverflow.com/questions/66251179/colors-must-be-argb-hex-values

    Don't ask me...
    """

    __old_rgb_set__ = RGB.__set__

    def __rgb_set_fixed__(self, instance, value):
        try:
            __old_rgb_set__(self, instance, value)
        except ValueError as e:
            if e.args[0] == "Colors must be aRGB hex values":
                __old_rgb_set__(self, instance, WHITE)  # Change color here

    RGB.__set__ = __rgb_set_fixed__

    return {}


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
