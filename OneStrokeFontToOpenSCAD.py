
line_segments_per_bezier_segment = 10

def IsSvgSeparator(character):
    if ( (character == ' ') or (character == '\t') or (character == ',') ):
        return True
    else:
        return False

def IsSvgNumeric(character):
    if ( ( (character >= '0') and (character <= '9') ) or (character == '-') or (character == '+')or (character == '.') or (character == 'e') or (character == 'E') ):
        return True
    else:
        return False

def TokenIsCommand(token):
    if ( token[0].isalpha()):
        return True
    else:
        return False

# This routine will take a path from an SVG file and split it into tokens
# e.g. 'M 400 700 C 400 700 412.58 476.14 400 166.66 C 387.59 85.13 346.72 19.84 266.6 -0'
# will be transformed into
# [ 'M','400','700','C','400','700','412.58','476.14','400','166.66','C','387.59','85.13','346.72','19.84','266.6','-0']
def SvgPathTextToTokens(svg_path_text):
    return_value = []
    if (svg_path_text != ""):
        index = 0
        while (index < len(svg_path_text)):
            # Skip over whitespace
            while ((index < len(svg_path_text)) and IsSvgSeparator(svg_path_text[index])):
                index = index + 1

            if (svg_path_text[index].isalpha()):
                return_value.append(svg_path_text[index])
                index = index + 1
            else:
                token = ""
                while (index < len(svg_path_text) and IsSvgNumeric(svg_path_text[index])):
                    token = token + svg_path_text[index]
                    index = index + 1
                return_value.append(token)
    return return_value

class Point:
    def __init__(self,x_ordinate,y_ordinate):
        self.x = x_ordinate
        self.y = y_ordinate
    def AddOffset(self,offset_point):
        self.x += offset_point.x
        self.y += offset_point.y

    def Scale(self, scale_factor):
        self.x *= scale_factor
        self.y *= scale_factor

def DecodeOrdinateFromString(ordinate_string):
    return float(ordinate_string)

def DecodePointFromStrings(x_ordinate_string, y_ordinate_string):
    return Point(DecodeOrdinateFromString(x_ordinate_string), DecodeOrdinateFromString(y_ordinate_string) )

class Line:
    def __init__(self,start_point,end_point):
        self.start = Point(start_point.x,start_point.y)
        self.end = Point(end_point.x,end_point.y)

    def ToOpenScadSource(self):
        return_value = "                [" + str(self.start.x) + ',' + str(self.start.y) + ',' + str(self.end.x) + ',' + str(self.end.y) + '],\n'
        return return_value

    def IsZeroLength(self):
        if (self.start.x == self.end.x) and (self.start.y == self.end.y):
            return True
        else:
            return False

    def Scale(self, scale_factor):
        self.start.Scale(scale_factor)
        self.end.Scale(scale_factor)



class CubicBezier:
    def __init__(self,start_point, control1_point, control2_point, end_point):
        self.start = start_point
        self.control1 = control1_point
        self.control2 = control2_point
        self.end = end_point

    def EvaluateOrdinate(self,poly,t):
        return poly[0] * (1 - t) * (1 - t) * (1 - t) + 3 * poly[1] * t * (1 - t) * (1 - t) + 3 * poly[2] * t * t * (1 - t) + poly[3] * t * t * t

    def EvaluatePoint(self,t):
        x_poly = [ self.start.x, self.control1.x, self.control2.x, self.end.x]
        y_poly = [ self.start.y, self.control1.y, self.control2.y, self.end.y]
        way_point = Point(self.EvaluateOrdinate(x_poly,t),self.EvaluateOrdinate(y_poly,t))
        return way_point

    def GetLineSegments(self):
        return_value = []
        current_point = self.start
        num_linear_segments = line_segments_per_bezier_segment

        for i in range(num_linear_segments):
            t = i / num_linear_segments
            way_point = self.EvaluatePoint(t)
            line_segment = Line(current_point,way_point)
            if (not line_segment.IsZeroLength()):
                return_value.append(line_segment)
            current_point = way_point

        line_segment = Line(current_point,self.end)
        if (not line_segment.IsZeroLength()):
            return_value.append(line_segment)
        return return_value

class CutPath:
    def TokensToLineSegments(self, tokens):
        return_value = []

        current_point = Point(0,0)
        segment_origin = current_point
        if ( (len(tokens) >= 3) and ( (tokens[0]=="M") or (tokens[0] == "m") ) ):
            current_point = DecodePointFromStrings(tokens[1], tokens[2])
            segment_origin = current_point
            index = 3

            while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                new_point = DecodePointFromStrings(tokens[index], tokens[index + 1])
                new_segment = Line(current_point, new_point)
                return_value.append(new_segment)
                current_point = new_point
                segment_origin = new_point
                index += 2

            while (index < len(tokens)):
                if (tokens[index] == 'L'):
                    # line to absolute
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_point = DecodePointFromStrings(tokens[index], tokens[index + 1])
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 2
                elif (tokens[index] == 'l'):
                    # line to relative
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_point = DecodePointFromStrings(tokens[index], tokens[index + 1])
                        new_point.x += current_point.x
                        new_point.y += current_point.y
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 2
                elif (tokens[index] == 'H'):
                    # horizontal line to absolute
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_x = DecodeOrdinateFromString(tokens[index])
                        new_point = Point(new_x, current_point.y)
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 1
                elif (tokens[index] == 'h'):
                    # horizontal line to relative
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_x = DecodeOrdinateFromString(tokens[index]) + current_point.x
                        new_point = Point(new_x, current_point.y)
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 1
                elif (tokens[index] == 'V'):
                    # vertical line to absolute
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_y = DecodeOrdinateFromString(tokens[index])
                        new_point = Point(current_point.x, new_y)
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 1
                elif (tokens[index] == 'v'):
                    # vertical line to relative
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        new_y = DecodeOrdinateFromString(tokens[index]) + current_point.y
                        new_point = Point(current_point.x, new_y)
                        new_segment = Line(current_point, new_point)
                        return_value.append(new_segment)
                        current_point = new_point
                        index += 1
                elif (tokens[index] == 'C'):
                    # cubic bezier curve absolute
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        control_point1 = DecodePointFromStrings(tokens[index], tokens[index + 1])
                        control_point2 = DecodePointFromStrings(tokens[index + 2], tokens[index + 3])
                        end_point = DecodePointFromStrings(tokens[index + 4], tokens[index + 5])
                        cubic_bezier_segment = CubicBezier(current_point, control_point1, control_point2, end_point)
                        line_segments = cubic_bezier_segment.GetLineSegments()
                        return_value += line_segments
                        current_point = end_point
                        index += 6
                elif (tokens[index] == 'c'):
                    # cubic bezier curve relative
                    index += 1
                    while (index < len(tokens) and not TokenIsCommand(tokens[index])):
                        control_point1 = DecodePointFromStrings(tokens[index], tokens[index + 1])
                        control_point2 = DecodePointFromStrings(tokens[index + 2], tokens[index + 3])
                        end_point = DecodePointFromStrings(tokens[index + 4], tokens[index + 5])
                        control_point1.AddOffset(current_point)
                        control_point2.AddOffset(current_point)
                        end_point.AddOffset(current_point)
                        cubic_bezier_segment = CubicBezier(current_point, control_point1, control_point2, end_point)
                        line_segments = cubic_bezier_segment.GetLineSegments()
                        return_value += line_segments
                        current_point = end_point
                        index += 6
                elif (tokens[index] == 'Z' or tokens[index] == 'z'):
                    # close curve
                    index += 1
                    new_segment = Line(current_point, segment_origin)
                    return_value.append(new_segment)
                elif (tokens[index] == 'M'):
                    # move absolute
                    index += 1
                    new_point = DecodePointFromStrings(tokens[index], tokens[index + 1])
                    current_point = new_point
                    segment_origin = new_point
                    index += 2
                elif (tokens[index] == 'm'):
                    # move relative
                    index += 1
                    new_point = DecodePointFromStrings(tokens[index], tokens[index + 1])
                    new_point.x += current_point.x
                    new_point.y += current_point.y
                    current_point = new_point
                    segment_origin = new_point
                    index += 2
                else:
                    # unexpected command type
                    print("Unexpected token " + tokens[index])
                    index += 1
        return return_value

    def SvgPathTextToLineSegments(self, svg_path_text):
        tokens = SvgPathTextToTokens(svg_path_text)
        return_value = self.TokensToLineSegments(tokens)
        return return_value

    def ToOpenScadSource(self):
        return_value = ""
        for segment in self.line_segments:
            return_value += segment.ToOpenScadSource()
        return return_value

    def Scale(self, scale_factor):
        for segment in self.line_segments:
            segment.Scale(scale_factor)

    def __init__(self,svg_path_text):
        self.line_segments = self.SvgPathTextToLineSegments(svg_path_text)


class Glyph:
    def __init__(self, attrib):
        self.attrib = attrib
        self.unicode = attrib['unicode']
        self.glyph_name = attrib['glyph-name']
        try:
            self.path_string = attrib['d']
        except:
            self.path_string = ''
        self.width = float(attrib['horiz-adv-x'])
        self.cut_path = CutPath(self.path_string)

    def Scale(self,scale_factor):
        # create a deep copy of the points here to avoid problems when the lines are scaled
        self.cut_path.Scale(scale_factor)
        self.width *= scale_factor

    def ToOpenScadSource(self):
        import html
        unescapedCharacter = html.unescape(self.unicode)
        unicodepoint = ord(unescapedCharacter)
        return_value = ""
        #return_value += '            [/* "' + self.unicode + '" */ ' + str(unicodepoint) + ',' + str(self.width) + ', [\n' 
        return_value += '            [ ' + str(unicodepoint) + ',' + str(self.width) + ', [\n' 
        return_value += self.cut_path.ToOpenScadSource()
        return_value += '            ]],\n'
        return return_value

class SvgFont:
    def __init__(self, filename):
        self.filename = filename
        self.glyphs = []
        import xml.etree.ElementTree as et
        tree = et.ElementTree(file=filename)
        root = tree.getroot()        

        print('Converting file "' + filename + '"')

        font_face = ""
        for font_face in root.iter('{http://www.w3.org/2000/svg}font-face'):
            font_face = font_face

        if (font_face != ""):
            ascent = float(font_face.attrib['ascent'])
            descent = float(font_face.attrib['descent'])
            height = ascent-descent
            self.font_name = font_face.attrib['font-family']
        else:
            height = 1000    
            self.font_name = "unknown"

        self.scale_factor = 1.0 / height

        for svg_glyph in root.iter('{http://www.w3.org/2000/svg}glyph'):
            attrib = svg_glyph.attrib
            new_glyph = Glyph(attrib)
            new_glyph.Scale(self.scale_factor)
            self.glyphs.append(new_glyph)

        print(str(len(self.glyphs)) + ' glyphs found')

    def ToOpenScadSource(self):
        return_value = '    [ "' + self.font_name + '",\n'
        return_value += '        [\n'
        for glyph in self.glyphs:
            return_value += glyph.ToOpenScadSource()
        return_value += '        ],\n'
        return_value += '    ],\n'
        return return_value

def ConvertFontsInDirectory(directory):

    import os
    file_list = []
    for file in os.listdir(directory):
        if file.endswith(".svg"):
            full_path_name = os.path.join(directory, file)
            file_list.append (full_path_name)

    with open('OneStrokeFonts.scad','w') as writer:
        writer.write('// File created by OneStrokeFontToOpenSCAD.py\n')
        writer.write('\n')
        writer.write('font_table =\n')
        writer.write('[\n')
 
        for file in file_list:
            font = SvgFont(file) 
            font_source_code = font.ToOpenScadSource()
            writer.write(font_source_code)
        writer.write('];\n')


ConvertFontsInDirectory('.\\')