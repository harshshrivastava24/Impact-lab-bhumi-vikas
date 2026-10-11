import { describe, expect, it } from 'vitest';
import { computeLayout, placeCallouts, scaleBarMetres, splitLabel, toSvgRect, toSvgX, toSvgY } from '../src/lib/geometry';

describe('computeLayout', () => {
  it('uses one scale factor that fits the larger dimension', () => {
    const l = computeLayout(10, 20);
    expect(l.scale).toBeCloseTo(19); // 380 / 20
    expect(l.plot.width).toBeCloseTo(190);
    expect(l.plot.height).toBeCloseTo(380);
  });

  it('rejects non-positive dimensions', () => {
    expect(() => computeLayout(0, 20)).toThrow();
  });
});

describe('coordinate mapping', () => {
  const l = computeLayout(10, 20);

  it('flips y so the road (y = 0) is at the bottom of the plot', () => {
    expect(toSvgY(l, 20, 0)).toBeCloseTo(l.plot.y + l.plot.height);
    expect(toSvgY(l, 20, 20)).toBeCloseTo(l.plot.y);
  });

  it('maps the A.5 front overlap strip to a 0.60 m tall box just above the front line', () => {
    const r = toSvgRect(l, 20, { x: 2.5, y: 2.4, width: 7.5, depth: 0.6 });
    expect(r.height).toBeCloseTo(0.6 * l.scale);
    expect(r.width).toBeCloseTo(7.5 * l.scale);
    expect(r.y + r.height).toBeCloseTo(toSvgY(l, 20, 2.4));
    expect(r.x).toBeCloseTo(toSvgX(l, 2.5));
  });
});

describe('placeCallouts', () => {
  it('keeps every label at least minGap apart, including multi-line labels', () => {
    const items = [
      { anchorY: 100, data: 'a', size: 40 },
      { anchorY: 101, data: 'b' },
      { anchorY: 102, data: 'c', size: 30 },
      { anchorY: 300, data: 'd' },
    ];
    const placed = placeCallouts(items, 30, 0, 1000);
    for (let i = 1; i < placed.length; i++) {
      const prev = placed[i - 1];
      const cur = placed[i];
      if (!prev || !cur) throw new Error('missing');
      expect(cur.labelY - prev.labelY).toBeGreaterThanOrEqual(Math.max(30, prev.size ?? 0));
    }
  });

  it('pulls the column up when labels would overflow the bottom', () => {
    const placed = placeCallouts(
      [
        { anchorY: 95, data: 'a' },
        { anchorY: 96, data: 'b' },
        { anchorY: 97, data: 'c' },
      ],
      20,
      0,
      100,
    );
    expect(placed.at(-1)?.labelY).toBe(100);
    expect(placed.map((p) => p.labelY)).toEqual([60, 80, 100]);
  });
});

describe('splitLabel', () => {
  it('splits long labels at a comma', () => {
    expect(splitLabel('Footprint 7.50 x 15.10 m, 113.25 sq m', 30)).toEqual(['Footprint 7.50 x 15.10 m,', '113.25 sq m']);
  });
  it('keeps short labels whole', () => {
    expect(splitLabel('Front 3.00 m, R56(1)(a)', 30)).toEqual(['Front 3.00 m, R56(1)(a)']);
  });
});

describe('scaleBarMetres', () => {
  it('is 1 m for small plots and 5 m otherwise', () => {
    expect(scaleBarMetres(10, 12)).toBe(1);
    expect(scaleBarMetres(10, 20)).toBe(5);
  });
});
