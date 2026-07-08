# TODO - ForensicTech UI updates

## 1) Top tab UI + active highlight
- [x] Update `utils/app_style.py` to style active tab (CSS + active class).
- [x] Update `render_top_tabs()` to apply active state based on query param `tab`.


## 2) Apply top tab theme consistently
- [x] Ensure pages `04_Network_Graph.py`, `05_Communication_Review.py`, `06_Case_Queue.py`, `07_Evidence_Pack.py`, `09_Din.py` call `render_page_shell()` (not old/side-bar themed layout).


## 3) Vendor Intelligence UI refactor
- [ ] In `pages/03_Vendor_Intelligence.py`, remove old “vendor field metrics” block.
- [ ] Add dropdown “Search Vendor”.
- [ ] Add a table with columns: Vendor ID, Country, Vendor Type, Bank Account, Invoices, Payments, Total Spend, Investigation Cases.
- [ ] Ensure OSINT and Registry Due Diligence section starts immediately after the table.

## 4) Vendor Intelligence due diligence start order
- [ ] Verify section order in `pages/03_Vendor_Intelligence.py`.

## 5) Testing
- [ ] Run `streamlit run app.py`.
- [ ] Validate: tab buttons + active highlight, updated page styling, vendor table renders correctly.

