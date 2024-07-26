"""Command 42 data formatters"""

import logging


_LOGGER = logging.getLogger(__name__)


class MessageB042DataDecoder:
    """Decode B0 42 message data.

    This is where we will incluide specific decoders for command 42 param responses.
    """

    def zero_padded_string_decoder(self, data: list[bytearray]) -> str | list[str]:
        """Decode zero padded encoded string identified as integer."""
        output = []
        for entry in data:
            # Rebuild each entry to 00 padded string
            entry = entry.decode("ascii", errors="ignore").rstrip("\x00")
            output.append(entry)

        if len(output) == 1:
            return output[0]

        return output

    def ff_terminated_string_decoder(self, data: list[bytearray]) -> str | list[str]:
        """Decode ff padded unencodedstring identified as integer."""
        output = []
        for entry in data:
            # Rebuild each entry to ff padded string
            entry = entry.hex().replace("ff", "")
            output.append(entry)

        if len(output) == 1:
            return output[0]

        return output

    def m42_80_00_decoder(self, data: list[bytearray]) -> str | list[str]:
        """Decode COMMS GPRS APN message.

        Data is array of 00 terminated strings but is encoded as integers
        """
        return self.zero_padded_string_decoder(data)

    def m42_81_00_decoder(self, data: list[bytearray]) -> dict:
        """Decode COMMS GPRS USER message.

        Data is array of 00 terminated strings but is encoded as integers
        """
        return self.zero_padded_string_decoder(data)

    def m42_82_00_decoder(self, data: list[bytearray]) -> dict:
        """Decode COMMS GPRS PWD message.

        Data is array of 00 terminated strings but is encoded as integers
        """
        return self.zero_padded_string_decoder(data)

    def m42_a4_00_decoder(self, data: list[bytearray]) -> dict:
        """Decode EMAIL ADDRESSES message.

        Data is array of 00 terminated strings but is encoded as integers
        """
        return self.zero_padded_string_decoder(data)

    def m42_a5_00_decoder(self, data: list[bytearray]) -> dict:
        """Decode PHONE NUMBERS message.

        Data is array of ff terminated strings but is encoded as integers
        """
        return self.ff_terminated_string_decoder(data)
