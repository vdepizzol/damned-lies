%.mo: %.po
	msgfmt -o $@ $<

LANGUAGES=$(shell cat LINGUAS)

all: $(LANGUAGES:=.mo)

