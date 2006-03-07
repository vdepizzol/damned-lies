
%.xml: %.xml.in
	intltool-merge -x . $< $@

all: gnome-modules.xml translation-teams.xml releases.xml
