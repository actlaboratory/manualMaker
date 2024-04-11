import os
import shutil
import subprocess
import tempfile


VAR_PREFIX: str = "_l_l_l_l_0000ACTLAB_"
CONTENTS_DIR: str = "contents"


class IndexObject():
    def __init__(self, title: str, path: str, mdDir: str,
                 indexLevel: int, isContentAvailable: bool):
        self.title: str = title
        self.path: str = path
        self.mdDir: str = mdDir
        self.indexLevel: int = indexLevel
        self.isContentAvailable: bool = isContentAvailable
        self.templateDir: str = ""
        self.templateFile: str = ""
        self.children: list[IndexObject] = []


class Main():
    def __init__(self):
        # 定義
        self.rootIndexTemplateStr: str = ""

    def createTemplate(
            self, indexObject: IndexObject,
            workDir: str, rootTitle: str = None) -> None:
        if rootTitle == None:
            rootTitle = indexObject.title
            title = rootTitle
        else:
            title = f'{indexObject.title} - {rootTitle}'
        template = ""
        with open("template.html", "r", encoding="UTF-8") as f:
            template = f.read()
        template = template.replace(
            VAR_PREFIX + "titleHeader", rootTitle)
        template = template.replace(
            VAR_PREFIX + "title", title)
        template = template.replace(
            VAR_PREFIX + "rootIndex", self.rootIndexTemplateStr)
        template = template.replace(
            VAR_PREFIX + "rootDir", ("../" * indexObject.indexLevel)[1:])
        indexObject.templateDir = os.path.join(
            workDir, indexObject.path)
        indexObject.templateFile = os.path.join(
            indexObject.templateDir, "template.html")
        if indexObject.templateDir == os.path.join(workDir, ""):
            shutil.rmtree(workDir, ignore_errors=True)
        os.mkdir(indexObject.templateDir)
        with open(indexObject.templateFile, "w", encoding="UTF-8") as f:
            f.write(template)
        for o in indexObject.children:
            self.createTemplate(o, workDir, rootTitle)

    def createIndexObject(self, rootTitle: str, dir: str, path: str = "",
                          level: int = 1) -> IndexObject:
        if rootTitle == "":
            title = os.path.basename(dir)[5:]
        else:
            title = rootTitle
        if len(path) > 0 and path[0] == "/":
            path = path[1:]
        obj: IndexObject = IndexObject(
            title=title,
            indexLevel=level,
            isContentAvailable=os.path.isfile(os.path.join(dir, "index.md")),
            path=path, mdDir=dir)
        dirs = [
            d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
        dirs.sort()
        for d in dirs:
            obj.children.append(self.createIndexObject(
                "", dir=os.path.join(dir, d),
                path=path + "/" + d[:4],
                level=level + 1))
        return obj

    def createRootIndexTemplateStr(
            self, indexObject: IndexObject) -> str:
        texts = [
            f'<ul id="rootIndex_{indexObject.path}" class="collapse">',
            f'<li><a href="{VAR_PREFIX}rootDir{indexObject.path}/index.html">'
            + f'{indexObject.title}</a></li>']
        for o in indexObject.children:
            if len(o.children) == 0:
                texts.append(
                    f'<li><a href="{VAR_PREFIX}rootDir{o.path}/index.html">'
                    + f'{o.title}</a></li>')
            else:
                texts.append(
                    f'<li><a href="#rootIndex_{o.path}"'
                    + ' data-bs-toggle="collapse" aria-expanded="false"'
                    + f' aria-controls="rootIndex_{o.path}">'
                    + f'{o.title}</a>')
                texts.append(self.createRootIndexTemplateStr(o))
                texts.append('</li>')
        texts.append('</ul>')
        return "\n".join(texts)

    def createChildrenIndexStr(self, indexObject: IndexObject) -> str:
        return ""

    def outputPageSet(self, indexObject: IndexObject, outputDir: str):
        htmlDir = os.path.join(outputDir, indexObject.path)
        htmlFile = os.path.join(htmlDir, "index.html")
        if htmlDir == os.path.join(outputDir, ""):
            shutil.rmtree(outputDir, ignore_errors=True)
            os.mkdir(htmlDir)
            shutil.copytree(
                "bootstrap-5.3.0-dist",
                os.path.join(outputDir, "bootstrap-5.3.0-dist"))
        else:
            os.mkdir(htmlDir)
        if indexObject.isContentAvailable:
            subprocess.run([
                "pandoc",
                f'--output={htmlFile}',
                f'--template={indexObject.templateFile}',
                os.path.join(indexObject.mdDir, "index.md")
            ])
        else:
            with tempfile.TemporaryFile("w", encoding="UTF-8") as f:
                f.write(f'% index\n\n## {indexObject.title}\n')
                f.seek(0)
                subprocess.run([
                    "pandoc",
                    f'--output={htmlFile}',
                    f'--template={indexObject.templateFile}'
                ], stdin=f, encoding="UTF-8")
        for o in indexObject.children:
            self.outputPageSet(o, outputDir)

main = Main()
io = main.createIndexObject("テスト", "contents")
idxTmpl = main.createRootIndexTemplateStr(io)
main.rootIndexTemplateStr = idxTmpl
main.createTemplate(io, "templateTmp")
main.outputPageSet(io, "htmlOutput")
