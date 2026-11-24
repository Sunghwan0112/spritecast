// Written by SpriteCast's export.py. Plays a SpriteCast character's animation by action and facing:
//     SpriteCastFacing.Play(GetComponent<Animator>(), "walk", "east");
// A facing the set has no drawing for (a set made with "facings": 4 has the diagonals only, "cardinal" the cardinals) shows the nearest
// one it has; between two as near (east: south-east or north-east; south-east: south or east) the one shown last on that Animator stays, so walking straight across does not flicker; with none shown
// yet, the one turned more toward the viewer.
using System.Collections.Generic;
using UnityEngine;

public static class SpriteCastFacing
{
    static readonly string[] Facings = { "south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west" };
    static readonly Dictionary<int, string> Shown = new Dictionary<int, string>();

    static int Hash(string action, string facing) => Animator.StringToHash((action + "_" + facing).Replace("-", "_"));

    static int ToViewer(string f) { int k = System.Array.IndexOf(Facings, f); return Mathf.Min(k, 8 - k); }

    public static bool Has(Animator animator, string action, string facing) => animator.HasState(0, Hash(action, facing));

    // the facing drawn for this action nearest to the one asked for (itself when it is drawn); null when the action has none
    public static string Nearest(Animator animator, string action, string facing)
    {
        if (Has(animator, action, facing)) return facing;
        Shown.TryGetValue(animator.GetInstanceID(), out var last);
        int i = System.Array.IndexOf(Facings, facing), bestD = 99; string best = null;
        for (int j = 0; j < Facings.Length; j++)
        {
            if (!Has(animator, action, Facings[j])) continue;
            int d = Mathf.Abs(i - j); d = Mathf.Min(d, 8 - d);
            // between two as near: the one shown last, else the one turned more toward the viewer (west: south-west)
            if (d < bestD || (d == bestD && best != last && (Facings[j] == last || ToViewer(Facings[j]) < ToViewer(best)))) { best = Facings[j]; bestD = d; }
        }
        return best;
    }

    public static void Play(Animator animator, string action, string facing)
    {
        var f = Nearest(animator, action, facing);
        if (f == null) return;
        Shown[animator.GetInstanceID()] = f;
        animator.Play(Hash(action, f));
    }
}
