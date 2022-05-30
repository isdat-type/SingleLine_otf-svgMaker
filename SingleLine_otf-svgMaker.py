# SingleLine otf-svgMaker, Robofont single-line OpenType SVG export script
# by Frederik Berlaen for isdaT-type, 2021 
# institut supérieur des arts et du design de Toulouse / isdaT
# isdaT-type https://github.com/isdat-type
# typography and type design public research program 
# coordination: François Chastanet
# development for Relief SingleLine font project
# https://github.com/isdat-type/Relief-SingleLine

import os
from operator import itemgetter

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.S_V_G_ import table_S_V_G_

from ufo2svg.svgPathPen import SVGPathPen
from outlinePen import OutlinePen

# set a line thickness
lineThickness = 40

# strokeColor = "rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})"
strokeColor = "currentColor"

# overwrite the existing SVGPathPen
# it closes the path on endPath which is not good
class OpenSVGPathPen(SVGPathPen):

    def endPath(self):
        self._lastCommand = None
        self._lastX = self._lastY = None

# get the current font
font = CurrentFont()
# loop over all glyphs in the font
for glyph in font:
    # create an outline layer
    dest = glyph.getLayer("outline")
    # clear that outline layer glyph
    dest.clear()
    dest.width = glyph.width
    dest.unicode = glyph.unicode
    # create an outline pen
    pen = OutlinePen(font, offset=lineThickness/2, connection="round", cap="round", optimizeCurve=True)
    # draw the source glyph in pen
    glyph.draw(pen)
    # set some pen drawing settings
    pen.drawSettings(drawOriginal=False, drawInner=True, drawOuter=True)
    # draw the pen into the dest layer glyph
    pen.draw(dest.getPen())
    # remove overlap
    dest.removeOverlap()

# create a path to generate the font
path = os.path.join(os.path.dirname(font.path), f"{font.info.familyName}-{font.info.styleName}_svg.otf")
# generate the font
font.generate(path=path, format="otf", layerName="outline")

################
# generate svg #
################

# generate svg per glyph/glyph index
def getSVGDocForGlyph(glyph, gid):
    # get the svg pen
    svgPen = OpenSVGPathPen(font)
    # draw the glyph into the svg pen
    glyph.draw(svgPen)
    # create the svg path data
    # colors are always 0-255
    svgPath = f'<path stroke="{strokeColor}" fill="none" stroke-width="{lineThickness}" stroke-linecap="round" stroke-linejoin="round" d="{svgPen.getCommands()}" />'
    # wrap it into a svg shape with transfrom
    svgData = f'<g transform="matrix(1 0 0 -1 0 0)">{svgPath}</g>'
    # build the svg
    return f'<svg id="glyph{gid}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{svgData}</svg>'

# open the binary font with fontTools
ft = TTFont(path)
# create an svg table
svg = table_S_V_G_("SVG ")
# set some default values
svg.version = 0
svg.docList = []
svg.colorPalettes = None
# get all glyph names
glyphOrder = ft.getGlyphOrder()
# loop over all glyphs in the font
for glyph in font:
    if glyph.name not in glyphOrder:
        # ignore ignored glyphs
        continue
    # get the glyph id
    gid = ft.getGlyphID(glyph.name)
    # generate the svg for that glyph
    svgDoc = getSVGDocForGlyph(glyph, gid)
    # add the svg document for that glyph index
    svg.docList.append((svgDoc, gid, gid))
# reorder by the glyph id
svg.docList = sorted(svg.docList, key=itemgetter(1))
# store the svg table in the binary font
ft["SVG "] = svg
# save the binary font
ft.save(path)
# close the font
ft.close()
# done!
print("done!")