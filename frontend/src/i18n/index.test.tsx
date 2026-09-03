import { render, screen, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { I18nProvider, useI18n } from "./index";
import LanguageSwitcher from "./LanguageSwitcher";

beforeEach(() => {
  window.localStorage.clear();
});

function Probe() {
  const { t, lang, dir } = useI18n();
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <span data-testid="dir">{dir}</span>
      <span data-testid="signout">{t("header.signOut")}</span>
      <span data-testid="interpolated">{t("app.deleteConfirm", { title: "Test" })}</span>
    </div>
  );
}

describe("i18n", () => {
  it("defaults to English LTR", () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("lang").textContent).toBe("en");
    expect(screen.getByTestId("dir").textContent).toBe("ltr");
    expect(screen.getByTestId("signout").textContent).toBe("Sign out");
  });

  it("interpolates params into translations", () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("interpolated").textContent).toBe('Delete "Test"?');
  });

  it("switches to Persian with RTL direction", () => {
    render(
      <I18nProvider>
        <LanguageSwitcher />
        <Probe />
      </I18nProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Change language" }));
    fireEvent.click(screen.getByText("فارسی"));

    expect(screen.getByTestId("lang").textContent).toBe("fa");
    expect(screen.getByTestId("dir").textContent).toBe("rtl");
    expect(screen.getByTestId("signout").textContent).toBe("خروج از حساب");
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("fa");
  });

  it("switches to German keeping LTR", () => {
    render(
      <I18nProvider>
        <LanguageSwitcher />
        <Probe />
      </I18nProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Change language" }));
    fireEvent.click(screen.getByText("Deutsch"));

    expect(screen.getByTestId("lang").textContent).toBe("de");
    expect(screen.getByTestId("dir").textContent).toBe("ltr");
    expect(screen.getByTestId("signout").textContent).toBe("Abmelden");
  });

  it("migrates a legacy team-project.language value", () => {
    window.localStorage.setItem("team-project.language", "fa");
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("lang").textContent).toBe("fa");
    expect(screen.getByTestId("dir").textContent).toBe("rtl");
  });
});
