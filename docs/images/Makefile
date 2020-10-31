PUMLs = $(wildcard *.puml)
PDFs = $(patsubst %.puml,%.pdf,$(PUMLs))
PNGs = $(patsubst %.puml,%.png,$(PUMLs))
SVGs = $(patsubst %.puml,%.svg,$(PUMLs))

all: $(PNGs) $(PDFs) $(SVGs)

%.pdf: %.puml
	plantuml -Tpdf $<

%.png: %.puml
	plantuml -Tpng $<

%.svg: %.puml
	plantuml -Tsvg $<


.PHONY: clean

clean:
	rm -f $(PDFs) $(PNGs) $(SVGs)
