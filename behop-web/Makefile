DOCS=$(wildcard *.jemdoc)

HDOCS=$(addsuffix .html, $(BDOCS))
BDOCS=$(basename $(DOCS))
PHDOCS=$(addprefix html/, $(HDOCS))

.PHONY : docs
docs : $(PHDOCS)

.PHONY : update
update : $(PHDOCS)
	@echo -n 'Copying to server...'
	scp -r html/* yiannisy@myth.stanford.edu:~/WWW/behop/
	@echo ' done.'

html/%.html : %.jemdoc
	./jemdoc.py -o $@ $<

.PHONY : clean
clean :
	-rm -f html/*.html
