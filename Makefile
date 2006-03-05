
gnome-modules.xml: gnome-modules.xml.in
	intltool-merge -x . $< $@
