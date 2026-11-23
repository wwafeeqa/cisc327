"""A4 end-to-end tests (Wafeeqa): the rental checkout and return workflow.

Each test creates its own equipment and renter through the web UI, using a
unique name, and finds its rows by that name or by the IDs the app assigned.
The app keeps data in memory and is never reset between tests, so this keeps
the tests independent of each other, of test order, and of anything already
on the server.

Run with the app running in another terminal:
    python -m pytest tests/e2e -v --headed
"""

import re
import uuid

from playwright.sync_api import Locator, Page, expect

# Column positions in the HTML tables (see app/templates/*.html).
EQUIPMENT_AVAILABLE_COL = 4
RENTAL_EQUIPMENT_COL, RENTAL_RENTER_COL = 1, 2
RENTAL_DATE_COL, RETURN_DATE_COL = 3, 5

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def unique(label: str) -> str:
    return f"{label} {uuid.uuid4().hex[:8]}"


def submit(page: Page, button: str) -> None:
    """Click a form's submit button and wait for the post-redirect page to load."""
    with page.expect_navigation():
        page.get_by_role("button", name=button).click()


def add_equipment(page: Page, name: str, category: str, total_units: int) -> str:
    """Add equipment through the Equipment page and return the ID the app gave it."""
    page.goto("/ui/equipment")
    page.get_by_label("Name").fill(name)
    page.get_by_label("Category").fill(category)
    page.get_by_label("Total Units").fill(str(total_units))
    submit(page, "Add Equipment")

    row = page.locator("tr", has_text=name)
    expect(row).to_have_count(1)
    return row.locator("td").first.inner_text()


def add_renter(page: Page, name: str, email: str) -> str:
    """Add a renter through the Renters page and return the ID the app gave them."""
    page.goto("/ui/renters")
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    submit(page, "Add Renter")

    row = page.locator("tr", has_text=name)
    expect(row).to_have_count(1)
    return row.locator("td").first.inner_text()


def check_out(page: Page, equipment_id: str, renter_id: str) -> None:
    page.goto("/ui/rentals")
    page.get_by_label("Equipment ID").fill(equipment_id)
    page.get_by_label("Renter ID").fill(renter_id)
    submit(page, "Check Out")


def available_units_cell(page: Page, equipment_name: str) -> Locator:
    page.goto("/ui/equipment")
    row = page.locator("tr", has_text=equipment_name)
    return row.locator("td").nth(EQUIPMENT_AVAILABLE_COL)


def rental_rows(page: Page, equipment_id: str, renter_id: str) -> list[Locator]:
    """Rows on the (already loaded) Rentals page for this equipment/renter pair."""
    rows = []
    for row in page.locator("table tr").all():
        cells = row.locator("td")
        if cells.count() == 0:  # header row
            continue
        if (
            cells.nth(RENTAL_EQUIPMENT_COL).inner_text() == equipment_id
            and cells.nth(RENTAL_RENTER_COL).inner_text() == renter_id
        ):
            rows.append(row)
    return rows


def test_check_out_and_return_equipment(page: Page):
    """Success: renting an item takes a unit, and returning it closes the
    rental and gives the unit back."""
    item = unique("Projector")
    equipment_id = add_equipment(page, item, "AV", total_units=2)
    renter_id = add_renter(page, unique("Ada Lovelace"), "ada@example.com")
    expect(available_units_cell(page, item)).to_have_text("2")

    # Check out: a new open rental appears on the Rentals page.
    check_out(page, equipment_id, renter_id)
    rows = rental_rows(page, equipment_id, renter_id)
    assert len(rows) == 1
    rental = rows[0]
    rental_date = rental.locator("td").nth(RENTAL_DATE_COL).inner_text()
    assert ISO_DATE.match(rental_date)
    expect(rental.locator("td").nth(RETURN_DATE_COL)).to_have_text("-")
    expect(rental.get_by_role("button", name="Return")).to_be_visible()

    # One unit is now out.
    expect(available_units_cell(page, item)).to_have_text("1")

    # Return: the rental gets a return date and can't be returned again.
    page.goto("/ui/rentals")
    rental = rental_rows(page, equipment_id, renter_id)[0]
    with page.expect_navigation():
        rental.get_by_role("button", name="Return").click()

    rental = rental_rows(page, equipment_id, renter_id)[0]
    # Compare with the server's own rental date rather than this machine's
    # clock, since the container runs in UTC and may be on a different day.
    expect(rental.locator("td").nth(RETURN_DATE_COL)).to_have_text(rental_date)
    expect(rental.get_by_role("button", name="Return")).to_have_count(0)

    # The unit is back.
    expect(available_units_cell(page, item)).to_have_text("2")


def test_cannot_check_out_more_units_than_exist(page: Page):
    """Boundary: once the only unit of an item is rented, a second checkout
    is rejected and the available count stays at zero."""
    item = unique("Tripod")
    equipment_id = add_equipment(page, item, "Camera", total_units=1)
    first_renter = add_renter(page, unique("Grace Hopper"), "grace@example.com")
    second_renter = add_renter(page, unique("Alan Turing"), "alan@example.com")

    # Rent the last (only) unit.
    check_out(page, equipment_id, first_renter)
    assert len(rental_rows(page, equipment_id, first_renter)) == 1
    expect(available_units_cell(page, item)).to_have_text("0")

    # Try to rent it again with nothing left.
    check_out(page, equipment_id, second_renter)
    assert rental_rows(page, equipment_id, second_renter) == [], (
        "a second rental was created for an item with no units left"
    )
    assert len(rental_rows(page, equipment_id, first_renter)) == 1
    expect(available_units_cell(page, item)).to_have_text("0")
