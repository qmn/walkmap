.PHONY: default clean
default: walkmap.svg

walkmap.svg: walkmap.py cambridge_streets.json
	./walkmap.py

cambridge_streets.json: walkmap.py
	./walkmap.py get

clean:
	rm -rf *.svg

deepclean:
	rm -rf *.svg *.json
