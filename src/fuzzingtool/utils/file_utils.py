# Copyright (c) 2021 Vitor Oriel <https://github.com/VitorOriel>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from os import walk

def readFile(fileName: str):
    """Reads content of a file.

    @type fileName: str
    @param fileName: The file path and name
    @returns list: The content into the file
    """
    try:
        with open(f'{fileName}', 'r') as thisFile:
            return [line.rstrip('\n') for line in thisFile if not line.startswith('#!')]
    except FileNotFoundError:
        raise Exception(f"File '{fileName}' not found")

def splitFilenames(files: list):
    """Splits the files, removing the extension and __init__.py

    @type files: list
    @param files: The filenames to split
    @returns list: The splited content, without extension
    """
    if '__init__.py' in files:
        files.remove('__init__.py')
    return [file.split('.')[0] for file in files]

def getPluginNamesFromCategory(category: str):
    """Gets the plugin filenames

    @type category: str
    @param category: The category of the plugins
    @returns list: The list with the plugin filenames
    """
    try:
        _, _, pluginFiles = next(walk(f"./fuzzingtool/core/plugins/{category}/"))
    except:
        from os.path import dirname, abspath
        _, _, pluginFiles = next(walk(f"{dirname(dirname(abspath(__file__)))}/core/plugins/{category}/"))
    return splitFilenames(pluginFiles)

def getReports():
    """Gets the report filenames
    
    @returns list: The list with the report filenames
    """
    try:
        _, _, reportFiles = next(walk(f"./fuzzingtool/reports/reports/"))
    except:
        from os.path import dirname, abspath
        _, _, reportFiles = next(walk(f"{dirname(dirname(abspath(__file__)))}/reports/"))
    return splitFilenames(reportFiles)