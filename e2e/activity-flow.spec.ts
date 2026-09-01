import { expect, test } from "@playwright/test";

test("member can create, view, and delete an activity", async ({ page }) => {
  const title = `E2E activity ${Date.now()}`;

  await page.goto("/users/hossein");
  await expect(page.getByRole("heading", { name: "Hossein", level: 1 })).toBeVisible();

  await page.getByLabel("Date").fill("2026-08-31");
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Add activity" }).click();

  const timelineItem = page.locator(".timeline-item").filter({ hasText: title });
  await expect(timelineItem).toBeVisible();

  const calendarDay = page.getByRole("button", { name: /^2026-08-31,/ });
  await calendarDay.click();
  await expect(page.locator(".calendar-detail")).toContainText(title);

  page.once("dialog", (dialog) => dialog.accept());
  await timelineItem.getByRole("button", { name: "Delete" }).click();
  await expect(page.locator(".timeline-item").filter({ hasText: title })).toHaveCount(0);
});
