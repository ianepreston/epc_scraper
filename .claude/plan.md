You are a senior data engineer building a web scraper of Emissions Performance
Credit data.

The main EPC page provides a list of all credits, and even offers an option to
export that full list to CSV. However, critical information is excluded from
that main data set, the original owner of the credit. This means that for
certain analysis that needs to know if the credit has been transferred, this
data is insufficient. From the main EPC page it is possible to load up a
specific page for any given credit where this information is available.

A sample of the data available from the main page is this

```
Registry	Vintage	Serial Start	Serial End	Quantity	Current Owner	Facility	Transaction Id	Status	Expiry Date	Compliance Year	Title
Emission Performance Credit	2024	1G52-24-0000000055450195	1G52-24-0000000055464902	14708	Acciona Wind Energy Canada Inc.	Magrath Wind Power Project	202506120025	Active	2030-07-05	0	2024 EPCs Under TIER
Emission Performance Credit	2024	1H37-24-0000000055479812	1H37-24-0000000055494719	14908	Acciona Wind Energy Canada Inc.	Chin Chute Wind Power Project	202506120025	Active	2030-07-05	0	2024 EPCs Under TIER
Emission Performance Credit	2024	1M09-24-0000000055516946	1M09-24-0000000055521897	4952	City of Medicine Hat,Electric Utility -Generation		202506300035	Pending Retirement	2030-07-05	2024	2024 EPCs Under TIER
Emission Performance Credit	2024	1G05-24-0000000055544434	1G05-24-0000000055555446	11013	TA Alberta Hydro	Barrier Hydro Plant		Active	2030-07-05	0	2024 EPCs Under TIER
Emission Performance Credit	2024	1G17-24-0000000055555447	1G17-24-0000000055579581	24135	TA Alberta Hydro	Bearspaw Hydro Plant		Active	2030-07-05	0	2024 EPCs Under TIER
```

On a more detailed page you'll find something like this:

```
EPC Serial Number: 	1G33-24-0000000055928008 to 1G33-24-0000000055937094
Current Owner (Facility):	TransCanada PipeLines Limited (TransCanada Alberta System)
Originating Owner (Facility):	TransAlta Renewables (Castle Wind Farm)
Vintage Year:	2024
Quantity:	9,087
Current Status:	Active
Expiry Date	2030-07-05
Transaction Id	202602270011
Province:	Alberta
Country:	Canada
```

The basic required flow is to scrape the multiple pages of credits listed
[here](https://alberta.csaregistries.ca/GHGR_Listing/EPC_Listing.aspx), use them
to retrieve the links to the detailed credits page for each credit, for example
[this one](https://alberta.csaregistries.ca/GHGR_Listing/EPC_SerialRangeDetail.aspx?SerialId=22812),
extract the data on that page, and then compile the results into a comprehensive
data set for each credit.

The scraping and extraction components should focus on returning the data as
pure python objects. Subsequent methods can be included to convert from the pure
python objects into formats for analysis, like files (csv, parquet) or
DataFrames (spark, pandas, polars).

The whole framework should be packaged up in uv so that end users can install
it, call a method or two, and get their data out.
