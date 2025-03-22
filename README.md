
## Flights Analysis Dashboard✈️
This project, developed by the **XB_0112 Data Engineering** group 8, provides an interactive dashboard built with Python and Streamlit to visualize airport and flight data—with features including **multi-language support, multi-page switching, real-time map visualization and flight path simulation using world city coordinates from worldcities.csv, dynamic data statistics, real-time data entry and query capabilities, and interactive sidebar controls.**
### Project Report && Project Inrtoduction
[Project Report](project%20report.md) && [flights_part1-4.pdf](flights_part1-4.pdf) 

## Dataset Overview
`flights_database.db` is an **SQLite database** containing all flights departing from **New York City (NYC)** in **2023**, along with relevant information. The database consists of the following **five tables**: 
* airlines : contains information of the airlines operating from NYC.
* airports
* flights : A very large table containing all (425,352) flights departing NYC in
2023 including flight information.
* planes : Information on the planes used.
* weather : hour-by-hour information on the weather in 2023.

`airports.csv` contains **information on all destination airports** for flights departing from **New York City in 2023**. Each row represents a **destination airport** where a flight from NYC landed. The dataset includes key details such as the airport's **FAA code, name, latitude, longitude, altitude, time zone, and daylight saving time information**.

`worldcities.csv` contains about 47 thousand unique cities and towns from every country in the world. [Source](https://simplemaps.com/data/world-cities)


## Project Features


- **Multi-Page Navigation**
  - The application is divided into several main pages:
    - **Flights Dashboard:**  
      - Displays dynamic visualizations and key statistics derived from flight data.
      - Features plots for delay distribution, flight volume for the three NYC airports, top destinations and flght intensity throughout the day.
      - The displayed information is interactive with possibilities to filter by departures airport and type of coloring.
    - **Delay analysis:**
      - Distinction between airport and specific route analysis
      - Presents key aggregation metrics, distribution over the months, top 5 delayed destinations by departure and arrival.
      - In specific route version, analysis on wind direction and impact available
    - **Date analysis:**  
      - Allows to choose a specific day in 2023
      - Insights on the flights volume, delays and operating airlines

- **Map Visualization**
  - Utilizes Plotly's Scatter Mapbox to render interactive maps showing airport locations.
  - Allows to view destinations from all the three NYC airports as well as choosing specific departure airport.
  - Three coloring options: by altitude, distance, or timezone.

- **Interactive Sidebar Controls**
  Depending on the page allows for
  - **Flight routes:** select the routes
  - **Delay analysis:** select the time frame and destination aiport.
      
## Installation & Setup
### Clone the repository
```bash
git clone https://github.com/Adel13Lis/group8-FlightsProject.git
```

### [optional] Create a virtual environment and activate it
Since macOS restricts global pip installation, the best solution is to create a virtual environment:
```bash
python3 -m venv myenv
source myenv/bin/activate  # open virtual environment on macOS/Linux
myenv\Scripts\activate     # virtual environment on Windows
^C #close the virtual environment
```

### Download libary
```bash
pip install -r requirements.txt
```
If you use Jupyter Notebook or Google Colab
```bash
!pip install -r requirements.txt
```
### Run
The analysis contained in the report
```bash
python3 src/flights.py
```
**Run the dashboard on your own machine**
```bash
streamlit run src/flights_dashboard.py
```

### Project Structure
```
PROJECTFLIGHTS-GROUP8/
|-- /.github/workflows/               # Auto test
│-- data/                             # Contains dataset files (e.g., CSVs)
│-- figures/                          # Stores generated visualizations (e.g., PNGs)
│-- src/                              # Source code directory
|    |-- explore.py                   # Exploration file for the data
|    |-- flights.py                   # Runnable Python file delivering quick analysis on the data
|    |-- flights_dashboard.py         # Python file containing the starting page of the streamlit dashboard
|    |-- pages/                       # Subpages used in the dashboard, NOT meant to run separately
|         |-- 1_Flight_Routes.py      
|         |-- 2_Delay_Analysis.py
|         |-- 3_Date_Analysis.py
│-- .gitignore            
│-- CONTRIBUTING.md                   # Guidelines for contributors
│-- project_introduction/             # Project Task Documents Folder
│-- project report.md                 # Detailed project report
│-- README.md                         # Project documentation
│-- flights_database.db               # Database
|-- flights_database.db-shm           # Temporary database file
|-- flights_database.db-wal           # Temporary database file
│-- flights_part1-4.pdf               # Assignment introduction
|-- project_report.md                 # Report on the assignment and obtained result
|-- requirements.txt                  # Required files for the program to run
```
### Git Collaboration Guidelines
[CONTRIBUTING.md](CONTRIBUTING.md)

### Git workflow
| Step | Command |
|------|---------|
| **Clone the repository** | `git clone https://github.com/oyoYnaY/projectFlights-group8.git` |
| **Fetch origin** | `git fetch origin` |
| **Create a new branch && Switch to the new branch** | `git checkout -b 6-add-linkes-to-readme` |
| **Switch to an existing branch** | `git checkout branch-name` |
| **Commit changes** | `git add . && git commit -m "Your commit message"` |
| **Push to remote repository** | `git push origin feature-branch-name` |
| **Create a Pull Request** | Navigate to GitHub → Click on "New Pull Request" |
| **Code review** | The team members review the code |
| **Merge PR** | `git merge feature-branch-name && git push origin main` |
| **Delete merged branch** | `git branch -d feature-branch-name && git push origin --delete feature-branch-name` |
| **Deploy the code** | Manually run `git pull` on the server |

Following this workflow ensures an organized and efficient development process. **Ensure You Always Fetch the Latest Code Before Making Changes.**

**If your local changes have not been committed, but you want to sync with the remote repository:**

Store your changes.
```bash
git stash
```
Sync with the remote repository.
```bash
git pull origin main
```
Get your changes.
```bash
git stash pop
```



