# RunPod SSH Key Setup - Quick Guide

## What's Happening

RunPod needs an SSH key to secure access to your pod. This is optional for most use cases, but RunPod prompts for it.

**For Graph of Thoughts: You don't actually need SSH access!** (We use HTTP API only)

## Two Options

### Option 1: Skip SSH (Recommended for GoT)

Since we're only using the vLLM HTTP API, you can skip SSH entirely:

1. **Don't generate SSH keys** (ignore the prompt)
2. **Continue deployment** without SSH
3. **Access via HTTP endpoint only** (which is what our scripts use)

**This is totally fine!** Our scripts only need the HTTP endpoint like:
```
https://your-pod-id-8000.proxy.runpod.net
```

### Option 2: Set Up SSH (Optional)

If you want SSH access for debugging or monitoring:

#### Step 1: Generate SSH Key

Run this command in your terminal:

```bash
ssh-keygen -t ed25519 -C "tadsligar@hotmail.com"
```

**Prompts you'll see:**

```
Enter file in which to save the key (/Users/tad/.ssh/id_ed25519):
```
- Just press **Enter** to use default location

```
Enter passphrase (empty for no passphrase):
```
- Press **Enter** for no passphrase (easier)
- Or type a passphrase for extra security

```
Enter same passphrase again:
```
- Press **Enter** again (or retype passphrase)

**Output:**
```
Your identification has been saved in /Users/tad/.ssh/id_ed25519
Your public key has been saved in /Users/tad/.ssh/id_ed25519.pub
```

#### Step 2: Copy Your Public Key

```bash
cat ~/.ssh/id_ed25519.pub
```

**Output looks like:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbCdEfGhIjKlMnOpQrStUvWxYz... tadsligar@hotmail.com
```

**Copy this entire line** (starts with `ssh-ed25519`)

#### Step 3: Add to RunPod

1. In RunPod deployment page:
   - Find **"SSH Public Keys"** section
   - Click **"Add SSH Key"**
   - Paste your public key
   - Give it a name (e.g., "My Mac")

2. Continue with deployment

#### Step 4: (Optional) Connect via SSH

Once pod is running:

```bash
# Get SSH command from RunPod dashboard
ssh root@your-pod-id-ssh.proxy.runpod.net -p 12345
```

---

## What You Actually Need for Graph of Thoughts

**Just the HTTP endpoint!** That's it.

Once your pod deploys:

1. Go to RunPod dashboard
2. Click your pod
3. Find **"Connect"** section
4. Copy the **HTTP Service** endpoint (port 8000)
   - Example: `https://abc123xyz-8000.proxy.runpod.net`

5. Update your config:
   ```yaml
   # configs/runpod_graph_of_thoughts.yaml
   vllm:
     base_url: https://abc123xyz-8000.proxy.runpod.net
   ```

**That's all you need!** No SSH required.

---

## Current Deployment Steps

Since you're at the SSH key prompt:

### Quick Path (Skip SSH):

1. **Close/ignore the SSH prompt**
2. **Continue to deployment**
3. **Wait for pod to start** (~5-10 min)
4. **Get HTTP endpoint** from dashboard
5. **Update config** file
6. **Run test!**

### Complete Path (With SSH):

1. **Open terminal** on your Mac
2. **Run:** `ssh-keygen -t ed25519 -C "tadsligar@hotmail.com"`
3. **Press Enter** 3 times (use defaults)
4. **Copy key:** `cat ~/.ssh/id_ed25519.pub`
5. **Paste into RunPod** SSH key field
6. **Continue deployment**
7. **Get HTTP endpoint** (same as above)

---

## RTX 6000 Ada - Excellent Choice!

**Specs:**
- **VRAM:** 48GB (perfect for Qwen 2.5 32B)
- **Architecture:** Ada Lovelace (newer than A6000)
- **Performance:** ~15-20% faster than A6000
- **Cost:** Similar to A6000 Spot pricing

**For Graph of Thoughts:**
- ✅ Model fits easily (needs ~20GB)
- ✅ Plenty of headroom for context (peak ~38GB)
- ✅ Faster than A6000 (better tokens/sec)
- ✅ Great choice!

**Expected performance:**
- Time/question: ~50s (vs ~55s on A6000)
- Full dataset: ~15 hours (vs ~16.5 on A6000)
- Cost (Spot): ~$4.20 (slightly cheaper due to speed)

---

## Next Steps After Deployment

1. **Wait for "Running" status** in RunPod dashboard

2. **Check logs** to see when model is loaded:
   - Click pod → Logs
   - Look for: `"Application startup complete"`

3. **Get HTTP endpoint:**
   - Connect section → HTTP Service (port 8000)
   - Copy URL

4. **Test endpoint:**
   ```bash
   curl https://YOUR_POD_ID-8000.proxy.runpod.net/health
   ```

   Should return: `{"status":"ok"}` or similar

5. **Update config:**
   ```bash
   # Edit this file
   nano configs/runpod_graph_of_thoughts.yaml

   # Change this line:
   base_url: https://YOUR_ACTUAL_POD_ID-8000.proxy.runpod.net
   ```

6. **Run quick test:**
   ```bash
   ./scripts/runpod_got_quickstart.sh
   # Choose option 1 (1 question test)
   ```

7. **If successful, run full evaluation!**

---

## Troubleshooting

### "SSH key required"
- **Solution:** Just skip it and continue
- **Or:** Follow Option 2 above to generate key

### "Can't find HTTP endpoint"
- **Look for:** "Connect" button on pod page
- **Port:** Should be 8000
- **Format:** `https://xxxxx-8000.proxy.runpod.net`

### "Pod stuck on 'Starting'"
- **Normal:** First start takes 5-10 minutes
- **Why:** Downloading ~20GB model
- **Check logs:** See download progress

### "Model not loading"
- **Check template:** Should be vLLM
- **Check model name:** `Qwen/Qwen2.5-32B-Instruct` (case-sensitive)
- **Check logs:** Look for errors

---

## Quick Summary

**For Graph of Thoughts, you only need:**

1. ✅ Deploy RTX 6000 Ada Spot with vLLM template
2. ✅ Wait for pod to start
3. ✅ Copy HTTP endpoint (port 8000)
4. ✅ Update config file
5. ✅ Run test!

**SSH is optional** - don't let it slow you down!

---

**Current Status:** You're on the SSH key step

**Recommendation:** Skip SSH and continue deployment

**Next:** Wait for pod to start, then get HTTP endpoint
