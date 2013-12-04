DOCS=$(wildcard *.jemdoc)

HDOCS=$(addsuffix .html, $(BDOCS))
BDOCS=$(basename $(DOCS))
PHDOCS=$(addprefix html/, $(HDOCS))

.PHONY : docs
docs : $(PHDOCS)

.PHONY : update
update : $(PHDOCS)
	@echo -n 'Copying to server...'
	sudo cp -r html/* /var/www/behop/
	@echo ' done.'

html/%.html : %.jemdoc
	./jemdoc.py -c behop.conf -o $@ $<

.PHONY : clean
clean :
	-rm -f html/*.html
