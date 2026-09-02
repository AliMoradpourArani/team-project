import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const studentPassword = "e2e-student-pass";
const professorPassword = "e2e-professor-pass";

async function signIn(page: Page, username: string, password: string) {
  await page.goto("/");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

test("student signs in and manages only their activity", async ({ page }) => {
  const title = `E2E activity ${Date.now()}`;
  await signIn(page, "hossein", studentPassword);

  await expect(page.getByRole("heading", { name: "Hossein", level: 1 })).toBeVisible();
  await expect(page).toHaveURL(/\/users\/hossein$/);

  await page.getByLabel("Date").fill("2026-09-01");
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Add activity" }).click();

  const timelineItem = page.locator(".timeline-item").filter({ hasText: title });
  await expect(timelineItem).toBeVisible();

  const calendarDay = page.getByRole("button", { name: /^2026-09-01,/ });
  await calendarDay.click();
  await expect(page.locator(".calendar-detail")).toContainText(title);

  page.once("dialog", (dialog) => dialog.accept());
  await timelineItem.getByRole("button", { name: "Delete" }).click();
  await expect(page.locator(".timeline-item").filter({ hasText: title })).toHaveCount(0);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("professor sees team overview and a read-only member drill-down", async ({ page }) => {
  await signIn(page, "professor", professorPassword);

  await expect(page).toHaveURL(/\/professor$/);
  await expect(page.getByText("Professor dashboard")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Team overview/i, level: 1 })).toBeVisible();
  await expect(page.locator(".professor-member-row")).toHaveCount(3);
  await expect(page.getByRole("heading", { name: "Project review queue" })).toBeVisible();

  await page.locator(".professor-member-row").filter({ hasText: "Hossein" }).click();
  await expect(page.getByText("Professor · read-only member view")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Hossein", level: 1 })).toBeVisible();
  await expect(page.getByRole("button", { name: "Add activity" })).toHaveCount(0);
  await expect(page.locator(".item-actions")).toHaveCount(0);
});

test("professor reviews a project and the student sees feedback read-only", async ({ page }) => {
  await signIn(page, "professor", professorPassword);
  await expect(page.getByRole("heading", { name: "Project review queue" })).toBeVisible();

  await page.locator(".review-queue-row").filter({ hasText: "Team Project Foundation" }).click();
  await expect(page.getByRole("heading", { name: /Start review|Update rubric/ })).toBeVisible();

  await page.getByLabel("Review status").selectOption("approved");
  await page.getByLabel("Functionality").fill("28");
  await page.getByLabel("Code quality").fill("18");
  await page.getByLabel("Documentation").fill("13");
  await page.getByLabel("Integration").fill("19");
  await page.getByLabel("Contribution").fill("14");
  await page.getByLabel("Feedback").fill("E2E professor feedback: approved for submission.");
  await page.getByRole("button", { name: "Save review" }).click();

  await expect(page.getByText("Review saved.")).toBeVisible();
  await expect(page.getByText("92/100")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await signIn(page, "hossein", studentPassword);
  await expect(page).toHaveURL(/\/users\/hossein$/);
  await page.goto("/projects/team-foundation");

  await expect(page.getByRole("heading", { name: "Approved" })).toBeVisible();
  await expect(page.getByText("92/100")).toBeVisible();
  await expect(page.getByText("E2E professor feedback: approved for submission.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Save review" })).toHaveCount(0);
});

test("student freezes an integrated project and professor sees delivery readiness", async ({ page }) => {
  await signIn(page, "hossein", studentPassword);
  await page.goto("/projects/team-foundation");

  await expect(page.getByRole("heading", { name: /Not submitted yet|Frozen submission/ })).toBeVisible();
  await page.getByRole("button", { name: /Submit frozen snapshot|Submit new frozen version/ }).click();
  await expect(page.getByText(/Submission v\d+ frozen successfully\./)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Frozen submission · v\d+/ })).toBeVisible();
  await expect(page.getByText("SHA-256", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await signIn(page, "professor", professorPassword);

  await expect(page.getByRole("heading", { name: "Final delivery control" })).toBeVisible();
  const teamProject = page
    .locator(".professor-submission-row")
    .filter({ hasText: "Team Project Foundation" });
  await expect(teamProject).toContainText(/v\d+/);
  await expect(page.getByText("Release blocked")).toBeVisible();
  await expect(page.getByRole("button", { name: "Freeze final release" })).toBeDisabled();
});
