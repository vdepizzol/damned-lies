VERSION=0.9

FILES=\
	AUTHORS \
	DESIGN \
	HACKING \
	INSTALL \
	Makefile \
	README \
	REQUIREMENTS \
	database.py \
	defaults.py \
	modules.py \
	potdiff.py \
	releases.py \
	teams.py \
	update-stats.py \
	utils.py \
	view-module.py \
	gnome-modules.xml.in \
	releases.xml.in \
	translation-teams.xml.in \
	data/cyan-bar.png \
	data/download.png \
	data/error.png \
	data/green-bar.png \
	data/info.png \
	data/main.css \
	data/nobody.png \
	data/purple-bar.png \
	data/red-bar.png \
	data/warn.png \
        templates/language-release-doc-stats-modules.tmpl \
        templates/language-release-doc-stats.tmpl \
        templates/language-release-ui-stats-modules.tmpl \
        templates/language-release-ui-stats.tmpl \
        templates/language-release.tmpl \
        templates/list-languages.tmpl \
        templates/list-modules.tmpl \
        templates/list-teams.tmpl \
        templates/module.tmpl \
        templates/show-stats.tmpl \
        templates/team.tmpl


%.xml: %.xml.in
	intltool-merge -x . $< $@

all: gnome-modules.xml translation-teams.xml releases.xml

dist: $(FILES)
	@mkdir -p damned-lies-$(VERSION) && \
	cp -rp $(FILES) damned-lies-$(VERSION) && \
	tar cvzf damned-lies-$(VERSION).tar.gz damned-lies-$(VERSION) && \
	rm -rf damned-lies-$(VERSION)

release: dist
	MYVERSION=`echo $(VERSION) | sed -e 's/\./_/g'` && cvs tag "damned_lies_$$MYVERSION"
