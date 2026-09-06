import uuid
from dataclasses import dataclass


def generate_tag() -> int:
    """
    Generate a random, unique tag.
    """
    # uuid version 4 creates a unique identifier without the for central repository checking.
    # Hashing converts the 128-bit uuid to integer for smaller memory and faster lookup
    return hash(uuid.uuid4())  

# Makes the tags immutable meaning could not be changed
# For slots, instead of a heavy dictionary, python allocates fixed amount of memory space
@dataclass(frozen=True, slots=True)  
class Tag:
    """
    Creates tag reference instances for the view to utilize.

    Once instantiated the tag values cannot be modified.
    """

    header: int
    body: int
    footer: int
    main_button: int
    clear_button: int
    plot_buffer_slider: int
    plot_height_slider: int
    plot_tab: int
    settings_tab: int
    settings_interface: int
    settings_channel: int
    settings_baudrate: int
    settings_apply: int
    settings_id_format: int

    def __init__(self) -> None:
        for tag_name in self.__slots__:
            object.__setattr__(self, tag_name, generate_tag())  # Since you cannot change the class and its attributes, this is used to assign a UUID to the tags
