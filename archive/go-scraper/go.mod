// Module manifest documenting the Go scraper dependencies.
// NOTE: The Go scrapers (main.go, commodity_scarp.go) remain source-only
// payload: main.go still points to a placeholder URL and both files declare
// package main, so no compiled Go binary is shipped by the installer.
module bazzar

go 1.22

require (
	fyne.io/fyne/v2 v2.5.2
	github.com/gocolly/colly/v2 v2.1.0
)
