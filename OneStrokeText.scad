include <OneStrokeFonts.scad>


// This is a model of the virtual V cutting bit
module VBit(d1,d2,h)
{
	cylinder(d1 = d1, d2 = d2, h = h,$fn = 20);
}


// Draw a straight line between two arbitrary points
module VBitCarvedLine(x1, y1, x2, y2, d1, d2, h)
{
	hull()
	{
		translate([x1, y1, 0])
			VBit(d1, d2, h);
		translate([x2, y2, 0])
			VBit(d1, d2, h);
	}
}

// Draw an array of lines
module VBitCarvedLineArray(lineArray, size, d1, d2, h)
{
    if (len(lineArray) > 0)
    {
        for(i=[0:len(lineArray)-1])
        {
            line = lineArray[i];
            VBitCarvedLine(line[0]*size, line[1]*size, line[2]*size, line[3]*size,d1, d2, h);
        }
    }
}

// Read the width of a single glyph from the font table
function CharacterWidth(glyph_table,unicodeCharacter) = 
    let(tableEntryIndexes = search (unicodeCharacter,glyph_table),
        tableEntry = glyph_table[tableEntryIndexes[0]] )
    tableEntry[1];

// Calculate the x position of a character within a rendered string
// This is calculated recursively as the offset of the previous character
// + the width of the previous character with a special case of the first character
// which has an offset of 0
function CharacterOffset(glyph_table,index,string) = index == 0 ? 0 : CharacterOffset(glyph_table,index-1,string) + CharacterWidth(glyph_table, ord(string[index-1]));


function FindFontFromFontName(font_name) = 
    let(tableEntryIndexes = search ([font_name],font_table),
        tableEntry = font_table[tableEntryIndexes[0]] )
    tableEntry;
    

module VbitText(text, size, font_name, d1, d2, h)
{
    font = font_name == "" ? font_table[0] : FindFontFromFontName(font_name);
    
    glyph_table = font[1];
    
    for(i=[0:len(text)-1])
    {
        unicodeForCharacterToRender = ord(text[i]);
        
        glyphTableEntryIndexes = search (unicodeForCharacterToRender,glyph_table);
        glyph = glyph_table[glyphTableEntryIndexes[0]];
        
        width = glyph[1];
        lineArray = glyph[2];
        
        x=CharacterOffset(glyph_table,i,text) * size;
        
        translate([x,0,0])
            VBitCarvedLineArray(lineArray, size, d1, d2, h);
    }
}

