// SpriteCast character importer for Unity (written by SpriteCast's export.py; the same file for every character).
// Copy the exported `unity/` folder's contents into Assets/. Each `<name>/<name>.spritecast.json` is then built by itself into:
//   <name>/<name>.prefab          root (Animator) > Shadow, Body, Effect (SpriteRenderers). The root's position is the point between the feet.
//   <name>/<name>.controller      one state per animation, named walk_south_east, idle_south, slash_east ...
//   <name>/Animations/*.anim      each clip sets the Body's, the Shadow's and the Effect's sprite, so they always go together
// Play one with:  GetComponent<Animator>().Play("walk_south_east");
// To build again by hand: Assets > SpriteCast > Build Characters.
#if UNITY_EDITOR
#pragma warning disable 0618   // TextureImporter.spritesheet: the plain way to slice, with no extra package
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class SpriteCastImporter
{
    [Serializable] class Shadow { public string png; public int[] cell; public int[] offset; }
    [Serializable] class Sheet { public string png; public int n; public int cols; }
    // an effect's cells run on over `sheets` in order (a big one is cut into several, each within the 4096 px a phone's GPU takes); without
    // the list (an export before it), the one sheet `png` with `n` cells, `cols` a row
    [Serializable] class Effect { public string png; public int[] cell; public int[] offset; public int n; public int per; public int cols; public Sheet[] sheets; }
    [Serializable] class Anim { public string name; public string png; public int n; public int[] cell; public float[] anchor; public float fps; public bool loop; public Shadow shadow; public Effect effect; }
    [Serializable] class Set { public string name; public float pixels_per_unit; public float shadow_alpha; public string first; public Anim[] anims; }

    const string Ext = ".spritecast.json";

    [MenuItem("Assets/SpriteCast/Build Characters")]
    public static void BuildAll()
    {
        int n = 0;
        foreach (var guid in AssetDatabase.FindAssets("t:TextAsset"))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid);
            if (p.EndsWith(Ext)) { Build(p); n++; }
        }
        Debug.Log($"SpriteCast: {n} character(s) built");
    }

    static Sprite[] Slice(string path, int n, int[] cell, Vector2 pivot, float ppu, int cols = 0)
    {
        if (cols <= 0) cols = n;                        // a strip; an effect's sheet has `cols` cells a row, the first row at the top
        int rows = (n + cols - 1) / cols;
        var ti = (TextureImporter)AssetImporter.GetAtPath(path);
        if (ti == null) throw new Exception("SpriteCast: " + path + " is missing");
        ti.textureType = TextureImporterType.Sprite;
        ti.spriteImportMode = SpriteImportMode.Multiple;
        ti.spritePixelsPerUnit = ppu;
        ti.mipmapEnabled = false;
        ti.alphaIsTransparency = true;
        ti.textureCompression = TextureImporterCompression.Uncompressed;
        ti.maxTextureSize = 8192;                       // a strip of 8 wide frames passes 2048: it must not be shrunk
        ti.npotScale = TextureImporterNPOTScale.None;
        var stem = Path.GetFileNameWithoutExtension(path);
        var meta = new SpriteMetaData[n];
        for (int i = 0; i < n; i++)
            meta[i] = new SpriteMetaData { name = $"{stem}_{i}", rect = new Rect((i % cols) * cell[0], (rows - 1 - i / cols) * cell[1], cell[0], cell[1]), alignment = (int)SpriteAlignment.Custom, pivot = pivot };
        ti.spritesheet = meta;
        ti.SaveAndReimport();
        var by = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().ToDictionary(s => s.name);
        return Enumerable.Range(0, n).Select(i => by[$"{stem}_{i}"]).ToArray();
    }

    static ObjectReferenceKeyframe[] Keys(Sprite[] s, float fps)
    {
        // one key a frame, and the last sprite once more at the end so the last frame lasts as long as the others
        var k = new List<ObjectReferenceKeyframe>();
        for (int i = 0; i < s.Length; i++) k.Add(new ObjectReferenceKeyframe { time = i / fps, value = s[i] });
        k.Add(new ObjectReferenceKeyframe { time = s.Length / fps, value = s[s.Length - 1] });
        return k.ToArray();
    }

    public static void Build(string jsonPath)
    {
        var set = JsonUtility.FromJson<Set>(File.ReadAllText(jsonPath));
        var dir = Path.GetDirectoryName(jsonPath).Replace('\\', '/');
        float ppu = set.pixels_per_unit > 0 ? set.pixels_per_unit : 100;
        if (!AssetDatabase.IsValidFolder(dir + "/Animations")) AssetDatabase.CreateFolder(dir, "Animations");
        var ctlPath = $"{dir}/{set.name}.controller";
        AssetDatabase.DeleteAsset(ctlPath);
        var ctl = AnimatorController.CreateAnimatorControllerAtPath(ctlPath);
        var sm = ctl.layers[0].stateMachine;
        Sprite firstBody = null, firstShadow = null;
        foreach (var a in set.anims)
        {
            // Unity's pivot is a fraction of the frame, counted from the bottom-left
            var body = Slice($"{dir}/{a.png}", a.n, a.cell, new Vector2(a.anchor[0] / a.cell[0], 1 - a.anchor[1] / a.cell[1]), ppu);
            Sprite[] shadow = null;
            if (a.shadow != null && !string.IsNullOrEmpty(a.shadow.png))
                shadow = Slice($"{dir}/{a.shadow.png}", a.n, a.shadow.cell,
                    new Vector2((a.anchor[0] - a.shadow.offset[0]) / a.shadow.cell[0], 1 - (a.anchor[1] - a.shadow.offset[1]) / a.shadow.cell[1]), ppu);
            // a swing's effect (water, flame, leaves ...): a third sprite over the body, `per` of its cells to each body frame
            Sprite[] effect = null; float efps = a.fps;
            if (a.effect != null && !string.IsNullOrEmpty(a.effect.png))
            {
                efps = a.fps * Mathf.Max(1, a.effect.per);
                var pivot = new Vector2((a.anchor[0] - a.effect.offset[0]) / a.effect.cell[0], 1 - (a.anchor[1] - a.effect.offset[1]) / a.effect.cell[1]);
                var sheets = a.effect.sheets != null && a.effect.sheets.Length > 0 ? a.effect.sheets : new[] { new Sheet { png = a.effect.png, n = a.effect.n, cols = a.effect.cols } };
                effect = sheets.SelectMany(s => Slice($"{dir}/{s.png}", s.n, a.effect.cell, pivot, ppu, s.cols)).ToArray();
            }
            var clip = new AnimationClip { frameRate = Mathf.Max(1, Mathf.Round(efps * 100) / 100) };
            AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("Body", typeof(SpriteRenderer), "m_Sprite"), Keys(body, a.fps));
            AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("Shadow", typeof(SpriteRenderer), "m_Sprite"),
                shadow != null ? Keys(shadow, a.fps) : new[] { new ObjectReferenceKeyframe { time = 0, value = null } });
            AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("Effect", typeof(SpriteRenderer), "m_Sprite"),
                effect != null ? Keys(effect, efps) : new[] { new ObjectReferenceKeyframe { time = 0, value = null } });
            var st = AnimationUtility.GetAnimationClipSettings(clip);
            st.loopTime = a.loop;
            AnimationUtility.SetAnimationClipSettings(clip, st);
            var clipPath = $"{dir}/Animations/{a.name}.anim";
            AssetDatabase.DeleteAsset(clipPath);
            AssetDatabase.CreateAsset(clip, clipPath);
            var state = sm.AddState(a.name);
            state.motion = clip;
            if (a.name == set.first) { sm.defaultState = state; firstBody = body[0]; firstShadow = shadow != null ? shadow[0] : null; }
        }
        var root = new GameObject(set.name);
        try
        {
            root.AddComponent<Animator>().runtimeAnimatorController = ctl;
            var sh = new GameObject("Shadow").AddComponent<SpriteRenderer>();
            sh.transform.SetParent(root.transform, false);
            sh.color = new Color(1, 1, 1, set.shadow_alpha > 0 ? set.shadow_alpha : 0.3f);
            sh.sortingOrder = -1;
            sh.sprite = firstShadow;
            var bd = new GameObject("Body").AddComponent<SpriteRenderer>();
            bd.transform.SetParent(root.transform, false);
            bd.sprite = firstBody;
            var fx = new GameObject("Effect").AddComponent<SpriteRenderer>();
            fx.transform.SetParent(root.transform, false);
            fx.sortingOrder = 1;
            PrefabUtility.SaveAsPrefabAsset(root, $"{dir}/{set.name}.prefab");
        }
        finally { UnityEngine.Object.DestroyImmediate(root); }
        AssetDatabase.SaveAssets();
        Debug.Log($"SpriteCast: {set.name}: {set.anims.Length} animations -> {dir}/{set.name}.prefab");
    }

    // a character dropped into the project is built by itself, once (when it has no prefab yet)
    class Watch : AssetPostprocessor
    {
        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            foreach (var p in imported)
            {
                if (!p.EndsWith(Ext)) continue;
                var prefab = p.Substring(0, p.Length - Ext.Length) + ".prefab";
                if (File.Exists(prefab)) continue;
                var path = p;
                EditorApplication.delayCall += () => { if (!File.Exists(prefab)) Build(path); };
            }
        }
    }
}
#endif
