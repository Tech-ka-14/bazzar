package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"sort"
	"sync"
	"time"

	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
	"github.com/gocolly/colly/v2"
)

type StockData struct {
	Ticker string
	Open   string
	High   string
	Low    string
	Close  string
	Volume string
}

var (
	scrapedData []StockData
	dataMutex   sync.Mutex
	pauseMutex  sync.Mutex
	pauseCond   *sync.Cond
	isPaused    bool
)

func init() {
	pauseCond = sync.NewCond(&pauseMutex)
}

func main() {
	// Initialize Fyne App
	myApp := app.New()
	myWindow := myApp.NewWindow("NSE/BSE Scraper - Data Ingestion")

	statusLabel := widget.NewLabel("Status: Waiting to start...")
	progressBar := widget.NewProgressBar()

	// Control Functions
	startScraping := func() {
		statusLabel.SetText("Status: Scraping in progress...")
		go runScraper(progressBar, statusLabel)
	}

	pauseScraping := func() {
		pauseMutex.Lock()
		isPaused = true
		pauseMutex.Unlock()
		statusLabel.SetText("Status: Paused")
	}

	resumeScraping := func() {
		pauseMutex.Lock()
		isPaused = false
		pauseCond.Broadcast() // Wake up the scraper
		pauseMutex.Unlock()
		statusLabel.SetText("Status: Scraping in progress...")
	}

	// UI Layout
	content := container.NewVBox(
		widget.NewLabel("Financial Terminal Scraper"),
		statusLabel,
		progressBar,
		container.NewHBox(
			widget.NewButton("Start", startScraping),
			widget.NewButton("Pause", pauseScraping),
			widget.NewButton("Resume", resumeScraping),
		),
	)

	myWindow.SetContent(content)
	myWindow.Resize(fyne.NewSize(400, 200))
	myWindow.ShowAndRun()
}

func runScraper(progress *widget.ProgressBar, status *widget.Label) {
	c := colly.NewCollector(
		colly.AllowedDomains("nseindia.com", "bseindia.com"),
		colly.Async(true),
	)

	// Header spoofing to avoid blocks
	c.OnRequest(func(r *colly.Request) {
		r.Headers.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
		r.Headers.Set("Accept", "text/html,application/json")
		
		// Thread-safe Pause Logic
		pauseMutex.Lock()
		for isPaused {
			pauseCond.Wait()
		}
		pauseMutex.Unlock()
	})

	c.OnHTML(".financial-row", func(e *colly.HTMLElement) {
		data := StockData{
			Ticker: e.ChildText(".ticker-symbol"),
			Open:   e.ChildText(".open-price"),
			High:   e.ChildText(".high-price"),
			Low:    e.ChildText(".low-price"),
			Close:  e.ChildText(".close-price"),
			Volume: e.ChildText(".volume"),
		}

		dataMutex.Lock()
		scrapedData = append(scrapedData, data)
		// Update Progress Safely on Main Thread
		progress.SetValue(float64(len(scrapedData)) / 5000.0) 
		dataMutex.Unlock()
	})

	// Add target URLs (In production, point to Bhavcopy zip)
	c.Visit("https://example-financial-site.com/market-data")
	c.Wait()

	// 1. Sort Data Alphabetically (Numbers first implicitly handled by ASCII)
	sort.Slice(scrapedData, func(i, j int) bool {
		return scrapedData[i].Ticker < scrapedData[j].Ticker
	})

	// 2. Write to CSV for DuckDB Ingestion
	writeToCSV()
	status.SetText("Status: Scraping Complete. Data Sorted and Exported.")
}

func writeToCSV() {
	file, err := os.Create("daily_ohlcv.csv")
	if err != nil {
		log.Fatal("Could not create CSV file", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	writer.Write([]string{"Ticker", "Open", "High", "Low", "Close", "Volume"})
	for _, d := range scrapedData {
		writer.Write([]string{d.Ticker, d.Open, d.High, d.Low, d.Close, d.Volume})
	}
}