import io

from sdl2 import rw_from_object

from sdl2 import (
    SDL_FreeSurface,  # https://wiki.libsdl.org/SDL_FreeSurface
    SDL_Color,
)

from sdl2.sdlttf import (
    TTF_OpenFontRW,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_15.html
    TTF_OpenFontIndexRW,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_17.html
    TTF_CloseFont,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_18.html
    TTF_FontFaceIsFixedWidth,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_34.html
    TTF_FontFaceFamilyName,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_35.html
    TTF_FontFaceStyleName,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_36.html
    TTF_RenderUTF8_Blended,  # https://www.libsdl.org/projects/SDL_ttf/docs/SDL_ttf_52.html
)

from ppb.assetlib import Asset, ChainingMixin, AbstractAsset, FreeingMixin
from ppb.systems._sdl_utils import ttf_call


class Font(ChainingMixin, FreeingMixin, AbstractAsset):
    """
    A True-Type/OpenType Font
    """
    def __init__(self, name, *, size, index=None):
        """
        * name: the filename to load
        * size: the size in points
        * index: the index of the font in a multi-font file (rare)
        """
        # We do it this way so that the raw data can be cached between multiple
        # invocations, even though we have to reparse it every time.
        self._data = Asset(name)
        self.size = size
        self.index = index

        self._start(self._data)

    def _background(self):
        self._file = rw_from_object(io.BytesIO(self._data.load()))
        # We have to keep the file around because freetype doesn't load
        # everything at once, resulting in segfaults.
        if self.index is None:
            return ttf_call(
                TTF_OpenFontRW, self._file, False, self.size,
                _check_error=lambda rv: not rv
            )
        else:
            return ttf_call(
                TTF_OpenFontIndexRW, self._file, False, self.size, self.index,
                _check_error=lambda rv: not rv
            )

    def free(self, data, _TTF_CloseFont=TTF_CloseFont):
        # ^^^ is a way to keep required functions during interpreter cleanup
        _TTF_CloseFont(data)  # Can't fail

    def __repr__(self):
        return f"<{type(self).__name__} name={self.name!r} size={self._size!r}{' loaded' if self.is_loaded() else ''}>"

    @property
    def name(self):
        return self._data.name

    def resize(self, size):
        """
        Returns a new copy of this font in a different size
        """
        return type(self)(self._data.name, size=size, index=self._index)

    @property
    def _is_fixed_width(self):
        return bool(TTF_FontFaceIsFixedWidth(self.load()))

    @property
    def _family_name(self):
        return TTF_FontFaceFamilyName(self.load())

    @property
    def _style_name(self):
        return TTF_FontFaceStyleName(self.load())


class Text(ChainingMixin, FreeingMixin, AbstractAsset):
    """
    A bit of rendered text
    """
    def __init__(self, txt, *, font, color=(0, 0, 0)):
        self.txt = txt
        self.font = font
        self.color = color

        self._start(self.font)

    def _background(self):
        return ttf_call(
            TTF_RenderUTF8_Blended, self.font.load(), self.txt.encode('utf-8'),
            SDL_Color(*self.color),
            _check_error=lambda rv: not rv
        )

    def free(self, object, _SDL_FreeSurface=SDL_FreeSurface):
        # ^^^ is a way to keep required functions during interpreter cleanup
        _SDL_FreeSurface(object)  # Can't fail
