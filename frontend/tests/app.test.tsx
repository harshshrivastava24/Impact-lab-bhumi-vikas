import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent, { type UserEvent } from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { App } from '../src/App';
import { LanguageProvider } from '../src/i18n/useStrings';
import { server } from '../src/mocks/server';

function setup() {
  const user = userEvent.setup();
  render(
    <LanguageProvider>
      <App />
    </LanguageProvider>,
  );
  return user;
}

async function fill(user: UserEvent, label: string | RegExp, value: string) {
  const input = screen.getByLabelText(label);
  await user.clear(input);
  await user.type(input, value);
}

async function appendixA(user: UserEvent) {
  await fill(user, /^Plot area/, '200');
  await fill(user, /^Road width/, '9');
  await fill(user, /^Proposed built-up area/, '250');
  await user.click(screen.getByRole('button', { name: 'Look up' }));
}

async function a5(user: UserEvent, height = '10') {
  await fill(user, /^Plot area/, '200');
  await fill(user, /^Road width/, '9');
  await fill(user, /^Proposed built-up area/, '250');
  await fill(user, /^Proposed building height/, height);
  await user.selectOptions(screen.getByLabelText(/^Development type/), 'semi_detached');
  await fill(user, /^Plot frontage/, '10');
  await fill(user, /^Plot depth/, '20');
  await fill(user, /^From front boundary/, '2.4');
  await fill(user, /^From rear boundary/, '2.5');
  await fill(user, /^From left boundary/, '2.5');
  await fill(user, /^From right boundary/, '0');
  await user.click(screen.getByRole('button', { name: 'Run plan check' }));
}

const figure = (label: string) => screen.getByRole('article', { name: label });

describe('Appendix A lookup', () => {
  it('shows every figure with its rule and page, the citation, version, amendment and disclaimer', async () => {
    const user = setup();
    await appendixA(user);

    expect(await screen.findByRole('heading', { name: /Rule 56\(1\)\(a\): Residential Buildings/ })).toBeInTheDocument();
    expect(within(figure('Front open space')).getByText('3.00')).toBeInTheDocument();
    expect(within(figure('Front open space')).getByRole('link', { name: 'Rule 56(1)(a), p. 77' })).toHaveAttribute('href', '/pdf/en#page=77');
    expect(within(figure('Rear open space')).getByText('2.50')).toBeInTheDocument();
    expect(within(figure('Maximum height')).getByText('12.50')).toBeInTheDocument();
    expect(within(figure('Permitted floor area')).getByText('250.00')).toBeInTheDocument();
    expect(within(figure('Application fee')).getByText('₹ 250')).toBeInTheDocument();
    expect(within(figure('Permission fee')).getByText('₹ 3,000')).toBeInTheDocument();
    expect(within(figure('Side open space')).getByText('Depends on development type. Clerk selects.')).toBeInTheDocument();

    const panel = within(screen.getByRole('main'));
    expect(panel.getByText(/Derived from MP Bhumi Vikas Rules 2012, consolidated to 6 March 2025/)).toBeInTheDocument();
    expect(panel.getAllByText('Potentially relevant amendment').length).toBeGreaterThan(0);
    expect(panel.getByText(/The building-permission clerk decides/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open EN PDF p. 77' })).toHaveAttribute('href', '/pdf/en#page=77');
    expect(screen.getByRole('link', { name: 'Open HI PDF p. 77' })).toHaveAttribute('href', '/pdf/hi#page=77');
    expect(screen.getByText('Result ready.')).toHaveAttribute('aria-live', 'polite');
  });

  it('reveals the calculation trace on request', async () => {
    const user = setup();
    await appendixA(user);
    const card = await screen.findByRole('article', { name: 'Permitted floor area' });
    await user.click(within(card).getByText('Show calculation'));
    expect(within(card).getByText('1.25 x 200 = 250 sq m, Rule 61 Table 8 row 1, p. 83')).toBeVisible();
  });
});

describe('validation', () => {
  it('blocks submit, names each missing field and focuses the summary', async () => {
    const user = setup();
    await user.click(screen.getByRole('button', { name: 'Look up' }));
    const summary = await screen.findByRole('heading', { name: 'Fix these fields before looking up' });
    expect(summary).toHaveFocus();
    expect(screen.getByRole('link', { name: 'Plot area is required.' })).toBeInTheDocument();
    expect(screen.getByLabelText(/^Plot area/)).toHaveAttribute('aria-invalid', 'true');
  });

  it('rejects a negative road width', async () => {
    const user = setup();
    await fill(user, /^Plot area/, '200');
    await fill(user, /^Road width/, '-3');
    await fill(user, /^Proposed built-up area/, '250');
    await user.click(screen.getByRole('button', { name: 'Look up' }));
    expect(await screen.findAllByText('Road width must be between 1 and 100 m.')).not.toHaveLength(0);
  });
});

describe('free text', () => {
  it('fills the form from a parsed question and outlines the filled fields', async () => {
    const user = setup();
    await user.type(screen.getByLabelText(/Type the question/), 'My plot is 200 sq m on a 9 m road');
    await user.click(screen.getByRole('button', { name: 'Fill form from text' }));
    await waitFor(() => expect(screen.getByLabelText(/^Plot area/)).toHaveValue('200'));
    expect(screen.getByLabelText(/^Road width/)).toHaveValue('9');
    expect(screen.getByLabelText(/^Plot area/).className).toContain('ring-info');
  });

  it('shows "Not found" with no rule or figure for a question outside the Rules', async () => {
    const user = setup();
    await user.type(screen.getByLabelText(/Type the question/), 'How do I pay my property tax online?');
    await user.click(screen.getByRole('button', { name: 'Fill form from text' }));
    await screen.findByText(/No plot details found in the text/);
    await user.click(screen.getByRole('button', { name: 'Look up' }));
    expect(await screen.findByRole('heading', { name: 'Not found in MP Bhumi Vikas Rules 2012' })).toBeInTheDocument();
    expect(screen.queryByText(/Rule 56/)).not.toBeInTheDocument();
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
    expect(screen.getByText(/The building-permission clerk decides/)).toBeInTheDocument();
  });
});

describe('Hindi', () => {
  it('shows Hindi labels while the rule text stays in English', async () => {
    const user = setup();
    await user.click(screen.getByRole('button', { name: 'हिन्दी' }));
    expect(document.documentElement.lang).toBe('hi');
    await fill(user, /^प्लॉट का क्षेत्रफल/, '200');
    await fill(user, /^सड़क की चौड़ाई/, '9');
    await user.click(screen.getByLabelText('आवेदन शुल्क'));
    await user.click(screen.getByLabelText('अनुज्ञा शुल्क'));
    await user.click(screen.getByRole('button', { name: 'खोजें' }));

    expect(await screen.findByRole('article', { name: 'सामने की न्यूनतम खुली जगह' })).toBeInTheDocument();
    expect(screen.getByText(/आधिकारिक हिन्दी पाठ हिन्दी PDF के पृष्ठ पर है/)).toBeInTheDocument();
    const ruleText = screen.getByRole('region', { name: '56(1)(a)' });
    expect(ruleText).toHaveAttribute('lang', 'en');
    expect(ruleText).toHaveTextContent('Up to 9.0 meters');
  });
});

describe('special cases', () => {
  it('narrow street in an existing developed area uses Rule 56(1)(b)', async () => {
    const user = setup();
    await fill(user, /^Plot area/, '200');
    await fill(user, /^Road width/, '5');
    await user.click(screen.getByLabelText('Yes'));
    await user.click(screen.getByLabelText('Application fee'));
    await user.click(screen.getByLabelText('Permission fee'));
    await user.click(screen.getByRole('button', { name: 'Look up' }));
    const card = await screen.findByRole('article', { name: 'Front open space' });
    expect(within(card).getByText('3.50')).toBeInTheDocument();
    expect(within(card).getByText('Rule 56(1)(b), p. 77')).toBeInTheDocument();
  });

  it('flags a development type outside Rule 53(1)(i)', async () => {
    const user = setup();
    await fill(user, /^Plot area/, '200');
    await fill(user, /^Road width/, '9');
    await fill(user, /^Plot frontage/, '14');
    await user.selectOptions(screen.getByLabelText(/^Development type/), 'semi_detached');
    await user.click(screen.getByLabelText('Application fee'));
    await user.click(screen.getByLabelText('Permission fee'));
    await user.click(screen.getByRole('button', { name: 'Look up' }));
    expect(await screen.findByText(/Frontage 14 m is outside that range/)).toBeInTheDocument();
  });

  it('shows a readable error card with retry when the service fails', async () => {
    server.use(http.post('/api/lookup', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })));
    const user = setup();
    await appendixA(user);
    expect(await screen.findByRole('heading', { name: 'Could not get a result' })).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    server.resetHandlers();
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('heading', { name: /Rule 56\(1\)\(a\)/ })).toBeInTheDocument();
  });

  it('shows a schema error instead of a blank screen for a malformed response', async () => {
    server.use(http.post('/api/lookup', () => HttpResponse.json({ status: 'answered' })));
    const user = setup();
    await appendixA(user);
    expect(await screen.findByText('The rule service sent a response in an unexpected format.')).toBeInTheDocument();
  });
});

describe('plan check (Appendix A.5)', () => {
  it('draws the plot, envelope, footprint and the 0.60 m front shortfall with rule and page', async () => {
    const user = setup();
    await a5(user);
    const drawing = await screen.findByRole('img', { name: /Plot 10.00 m by 20.00 m/ });
    expect(drawing).toHaveAccessibleName(/Buildable envelope 7.50 m by 14.50 m. Proposed footprint 7.50 m by 15.10 m. Setback conflict found/);
    expect(within(drawing).getByText('0.60 m short, R56(1)(a), p. 77')).toBeInTheDocument();
    expect(within(drawing).getByText('108.75 sq m')).toBeInTheDocument();
    expect(within(drawing).getByText('113.25 sq m')).toBeInTheDocument();

    const front = screen.getByRole('row', { name: /Front/ });
    expect(within(front).getAllByRole('cell').map((c) => c.textContent)).toEqual(['3.00 m', '2.40 m', '0.60 m', 'Rule 56(1)(a), p. 77']);
    const panel = within(screen.getByRole('main'));
    expect(panel.getByText('Setback conflict found')).toBeInTheDocument();
    expect(panel.getByText('Parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked')).toBeInTheDocument();
    expect(within(screen.getByRole('article', { name: 'Ground coverage' })).getByText('54.4')).toBeInTheDocument();
  });

  it('re-sends on a height edit and announces the changed side', async () => {
    const user = setup();
    await a5(user);
    await screen.findByRole('img', { name: /Plot 10.00 m/ });
    await fill(user, /^Proposed building height/, '10.5');
    expect(await screen.findByText('Left open space changed from 2.50 m to 3.00 m because the height changed.', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(within(screen.getByRole('row', { name: /Left/ })).getAllByRole('cell')[2]).toHaveTextContent('0.50 m');
  });

  it('keeps the hatch and adds a note when the clerk marks an exception', async () => {
    const user = setup();
    await a5(user);
    const drawing = await screen.findByRole('img', { name: /Plot 10.00 m/ });
    await user.selectOptions(screen.getByLabelText('Front'), 'garage_side_rear');
    expect(within(drawing).getByText('0.60 m short, R56(1)(a), p. 77')).toBeInTheDocument();
    // The note wraps onto two lines in the callout column.
    expect(within(drawing).getByText('clerk-marked exception,')).toBeInTheDocument();
    expect(within(drawing).getByText('see Rule 56(4)')).toBeInTheDocument();
  });

  it('blocks on an area mismatch and resolves with the dimensions', async () => {
    const user = setup();
    await a5(user);
    await screen.findByRole('img', { name: /Plot 10.00 m/ });
    await fill(user, /^Plot area/, '230');
    await user.click(screen.getByRole('button', { name: 'Run plan check' }));
    expect(await screen.findByRole('heading', { name: /Plan check stopped/ })).toBeInTheDocument();
    expect(screen.getByText(/Entered dimensions give 200.00 sq m; stated plot area is 230.00 sq m/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Use dimensions as plot area' }));
    expect(await screen.findByRole('img', { name: /Plot 10.00 m/ })).toBeInTheDocument();
    expect(screen.getByLabelText(/^Plot area/)).toHaveValue('200');
  });

  it('"Correct inputs" moves focus to plot area', async () => {
    const user = setup();
    await a5(user);
    await screen.findByRole('img', { name: /Plot 10.00 m/ });
    await fill(user, /^Plot area/, '230');
    await user.click(screen.getByRole('button', { name: 'Run plan check' }));
    await user.click(await screen.findByRole('button', { name: 'Correct inputs' }));
    expect(screen.getByLabelText(/^Plot area/)).toHaveFocus();
  });

  it('refuses a corner plot and shows both readings', async () => {
    const user = setup();
    await user.click(screen.getByLabelText('Two or more streets (corner plot)'));
    await a5(user);
    expect(await screen.findByRole('heading', { name: 'Plan check not available for this case' })).toBeInTheDocument();
    expect(screen.getByText(/the street facing the plot/)).toBeInTheDocument();
    expect(screen.getByText(/Reading one applies the wider street/)).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /Plot/ })).not.toBeInTheDocument();
  });

  it('Enter in a footprint field runs the plan check', async () => {
    const user = setup();
    await fill(user, /^Plot area/, '200');
    await fill(user, /^Road width/, '9');
    await fill(user, /^Proposed built-up area/, '250');
    await fill(user, /^Proposed building height/, '10');
    await user.selectOptions(screen.getByLabelText(/^Development type/), 'semi_detached');
    await fill(user, /^Plot frontage/, '10');
    await fill(user, /^Plot depth/, '20');
    await fill(user, /^From front boundary/, '2.4');
    await fill(user, /^From rear boundary/, '2.5');
    await fill(user, /^From left boundary/, '2.5');
    await fill(user, /^From right boundary/, '0{Enter}');
    expect(await screen.findByRole('img', { name: /Plot 10.00 m/ })).toBeInTheDocument();
  });
});
