import os, json, re, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from decimal import Decimal, InvalidOperation

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(APP_DIR, "quotation_template.png")

LANGUAGES = [
    "English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam", "Marathi",
    "Bengali", "Gujarati", "Punjabi", "Urdu", "Odia", "Spanish", "French",
    "Arabic"
]

def money(value):
    try:
        return f"{Decimal(str(value or 0)):,.2f}"
    except (InvalidOperation, ValueError):
        return "0.00"

class QuotationApp:
    def __init__(self, root):
        self.root = root
        root.title("Advita Enterprises — Quotation Generator")
        root.geometry("1120x850")
        root.minsize(900, 700)
        self.blue = "#064b9b"
        self.navy = "#092754"
        self.light = "#e7f0fb"
        self.items = []
        self._build()

    def _build(self):
        header = tk.Frame(self.root, bg=self.navy, padx=18, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="ADVITA ENTERPRISES", font=("Georgia", 22, "bold"),
                 fg="white", bg=self.navy).pack(anchor="w")
        tk.Label(header, text="QUALITY  |  TRUST  |  GROWTH  •  Quotation Generator",
                 font=("Arial", 10, "bold"), fg="#dceaff", bg=self.navy).pack(anchor="w", pady=(3,0))

        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        api = ttk.LabelFrame(self.body, text="Gemini AI", padding=10)
        api.pack(fill="x", pady=(0,10))
        ttk.Label(api, text="Gemini API key:").grid(row=0,column=0,sticky="w")
        self.api_key = tk.StringVar(value=os.environ.get("GEMINI_API_KEY",""))
        ttk.Entry(api, textvariable=self.api_key, show="*", width=54).grid(row=0,column=1,sticky="ew",padx=8)
        ttk.Label(api, text="Quotation language:").grid(row=0,column=2,sticky="w",padx=(12,4))
        self.language = tk.StringVar(value="English")
        ttk.Combobox(api, textvariable=self.language, values=LANGUAGES, state="readonly", width=16).grid(row=0,column=3,sticky="w")
        api.columnconfigure(1, weight=1)
        ttk.Label(api, text="Enter a product/service brief below. Gemini can suggest descriptions, quantities and prices; review all figures before issuing.",
                  foreground="#4d5d72", wraplength=900).grid(row=1,column=0,columnspan=4,sticky="w",pady=(8,0))

        customer = ttk.LabelFrame(self.body, text="Customer and quotation details", padding=10)
        customer.pack(fill="x", pady=(0,10))
        self.fields = {}
        specs = [
            ("to","To / Company",0,0), ("customer","Customer name",0,2),
            ("address","Address",1,0), ("phone","Phone number",2,0),
            ("email","Email",2,2), ("quote_no","Quotation number",3,0),
            ("quote_date","Date (DD/MM/YYYY)",3,2), ("validity","Validity",4,0),
            ("gst","GST %",4,2), ("payment","Payment terms",5,0),
            ("delivery","Delivery time",5,2),
        ]
        defaults = {"quote_no":"AE/QT/001","quote_date":date.today().strftime("%d/%m/%Y"),
                    "validity":"15 days","gst":"18","payment":"As agreed","delivery":"As agreed"}
        for key,label,r,c in specs:
            ttk.Label(customer,text=label+":").grid(row=r,column=c,sticky="w",padx=(0,6),pady=4)
            var=tk.StringVar(value=defaults.get(key,""))
            self.fields[key]=var
            ttk.Entry(customer,textvariable=var,width=40).grid(row=r,column=c+1,sticky="ew",padx=(0,14),pady=4)
        customer.columnconfigure(1,weight=1); customer.columnconfigure(3,weight=1)

        brief = ttk.LabelFrame(self.body, text="Describe what you are quoting", padding=10)
        brief.pack(fill="x", pady=(0,10))
        self.brief = tk.Text(brief, height=4, wrap="word", font=("Arial",10))
        self.brief.pack(fill="x")
        self.brief.insert("1.0","Example: Supply and installation of 5 desktop computers, include suitable specifications and market-based estimated prices in INR.")
        controls=ttk.Frame(brief); controls.pack(fill="x",pady=(8,0))
        self.generate_btn=ttk.Button(controls,text="Generate items with Gemini",command=self.generate)
        self.generate_btn.pack(side="left")
        ttk.Button(controls,text="Clear items",command=self.clear_items).pack(side="left",padx=8)
        ttk.Label(controls,text="AI prices are estimates; verify before sending.",foreground="#9b3d00").pack(side="left",padx=8)

        itemframe=ttk.LabelFrame(self.body,text="Quotation line items (editable)",padding=8)
        itemframe.pack(fill="both",expand=True,pady=(0,10))
        cols=("description","qty","price")
        self.tree=ttk.Treeview(itemframe,columns=cols,show="headings",height=10)
        self.tree.heading("description",text="Description of goods / services")
        self.tree.heading("qty",text="Qty")
        self.tree.heading("price",text="Unit price (₹)")
        self.tree.column("description",width=680); self.tree.column("qty",width=80,anchor="center"); self.tree.column("price",width=140,anchor="e")
        self.tree.pack(fill="both",expand=True,side="top")
        edit=ttk.Frame(itemframe); edit.pack(fill="x",pady=(8,0))
        self.desc_var=tk.StringVar(); self.qty_var=tk.StringVar(value="1"); self.price_var=tk.StringVar(value="0")
        ttk.Label(edit,text="Description").pack(side="left")
        ttk.Entry(edit,textvariable=self.desc_var,width=48).pack(side="left",padx=5)
        ttk.Label(edit,text="Qty").pack(side="left")
        ttk.Entry(edit,textvariable=self.qty_var,width=7).pack(side="left",padx=5)
        ttk.Label(edit,text="Unit ₹").pack(side="left")
        ttk.Entry(edit,textvariable=self.price_var,width=12).pack(side="left",padx=5)
        ttk.Button(edit,text="Add item",command=self.add_item).pack(side="left",padx=3)
        ttk.Button(edit,text="Update selected",command=self.update_item).pack(side="left",padx=3)
        ttk.Button(edit,text="Remove selected",command=self.remove_item).pack(side="left",padx=3)
        self.tree.bind("<<TreeviewSelect>>",self.select_item)

        bottom=ttk.Frame(self.body); bottom.pack(fill="x",pady=(0,8))
        self.total_label=ttk.Label(bottom,text="Subtotal: ₹0.00    GST: ₹0.00    Total: ₹0.00",font=("Arial",11,"bold"))
        self.total_label.pack(side="left")
        ttk.Button(bottom,text="Preview quotation",command=self.preview_pdf).pack(side="right")
        self.print_btn=ttk.Button(bottom,text="Print quotation",command=self.print_pdf,state="disabled")
        self.print_btn.pack(side="right",padx=8)
        ttk.Button(bottom,text="Export quotation PDF",command=self.export_pdf).pack(side="right",padx=8)
        ttk.Button(bottom,text="Save quotation data (JSON)",command=self.save_json).pack(side="right",padx=8)
        ttk.Label(self.body,text="Company details and blue quotation artwork are built into the PDF template. Always review generated translations, item details, GST and prices.",
                  foreground="#4d5d72",wraplength=1000).pack(anchor="w",pady=(0,8))

    def add_item(self):
        desc=self.desc_var.get().strip()
        if not desc:
            messagebox.showwarning("Missing description","Enter an item description."); return
        try:
            qty=float(self.qty_var.get()); price=float(self.price_var.get())
            if qty<=0 or price<0: raise ValueError()
        except ValueError:
            messagebox.showwarning("Invalid amount","Quantity must be above zero and price cannot be negative."); return
        self.tree.insert("", "end", values=(desc,qty,price))
        self.desc_var.set(""); self.qty_var.set("1"); self.price_var.set("0")
        self.update_totals()

    def select_item(self,event=None):
        sel=self.tree.selection()
        if sel:
            vals=self.tree.item(sel[0],"values")
            self.desc_var.set(vals[0]); self.qty_var.set(vals[1]); self.price_var.set(vals[2])

    def update_item(self):
        sel=self.tree.selection()
        if not sel: return
        try:
            qty=float(self.qty_var.get()); price=float(self.price_var.get())
            if qty<=0 or price<0: raise ValueError()
        except ValueError:
            messagebox.showwarning("Invalid amount","Quantity must be above zero and price cannot be negative."); return
        self.tree.item(sel[0],values=(self.desc_var.get().strip(),qty,price))
        self.update_totals()

    def remove_item(self):
        for s in self.tree.selection(): self.tree.delete(s)
        self.update_totals()

    def clear_items(self):
        for s in self.tree.get_children(): self.tree.delete(s)
        self.update_totals()

    def get_items(self):
        result=[]
        for row in self.tree.get_children():
            d,q,p=self.tree.item(row,"values")
            result.append({"description":d,"quantity":float(q),"unit_price":float(p)})
        return result

    def update_totals(self):
        subtotal=sum(x["quantity"]*x["unit_price"] for x in self.get_items())
        try: gst=max(0,float(self.fields["gst"].get() or 0))
        except ValueError: gst=0
        tax=subtotal*gst/100
        self.total_label.config(text=f"Subtotal: ₹{money(subtotal)}    GST: ₹{money(tax)}    Total: ₹{money(subtotal+tax)}")

    def generate(self):
        key=self.api_key.get().strip()
        brief=self.brief.get("1.0","end").strip()
        if not key:
            messagebox.showwarning("API key required","Enter your Gemini API key. You can obtain one from Google AI Studio."); return
        if not brief:
            messagebox.showwarning("Brief required","Describe the goods or services first."); return
        self.generate_btn.config(state="disabled",text="Generating…")
        threading.Thread(target=self._generate_thread,args=(key,brief),daemon=True).start()

    def _generate_thread(self,key,brief):
        try:
            from google import genai
            client=genai.Client(api_key=key)
            prompt=f"""Create quotation line items based on this request. Output ONLY valid JSON with this schema:
{{"items":[{{"description":"string","quantity":1,"unit_price":100.0}}]}}
Quotation language: {self.language.get()}
Request: {brief}
Use INR prices as sensible estimates if no prices were provided. Keep descriptions concise and suitable for a formal quotation. Return 1 to 10 items. Do not include markdown."""
            response=client.models.generate_content(model="gemini-2.5-flash",contents=prompt)
            raw=response.text or ""
            raw=re.sub(r"^```(?:json)?\s*|\s*```$","",raw.strip(),flags=re.I)
            data=json.loads(raw)
            items=data.get("items",[])
            if not isinstance(items,list) or not items: raise ValueError("Gemini did not return any line items.")
            clean=[]
            for item in items[:10]:
                clean.append((str(item.get("description","Item"))[:240],float(item.get("quantity",1)),float(item.get("unit_price",0))))
            self.root.after(0,self._apply_generated,clean)
        except Exception as e:
            self.root.after(0,lambda: messagebox.showerror("Gemini error",f"Could not generate quotation items.\\n\\n{e}\\n\\nCheck your API key, internet connection, and installed packages."))
        finally:
            self.root.after(0,lambda:self.generate_btn.config(state="normal",text="Generate items with Gemini"))

    def _apply_generated(self,items):
        self.clear_items()
        for d,q,p in items:
            self.tree.insert("","end",values=(d,q,p))
        self.update_totals()
        messagebox.showinfo("Items generated","Review every description, quantity and price before exporting.")

    def quotation_data(self):
        return {"language":self.language.get(),"fields":{k:v.get() for k,v in self.fields.items()},
                "items":self.get_items(),"brief":self.brief.get("1.0","end").strip()}

    def save_json(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],initialfile="quotation.json")
        if not path:return
        with open(path,"w",encoding="utf-8") as f: json.dump(self.quotation_data(),f,ensure_ascii=False,indent=2)
        messagebox.showinfo("Saved",f"Quotation data saved to:\\n{path}")

    def _validate_for_pdf(self):
        items=self.get_items()
        if not items:
            messagebox.showwarning("No items","Add or generate at least one line item before creating a PDF.")
            return None
        if not os.path.exists(TEMPLATE):
            messagebox.showerror("Template missing","quotation_template.png was not found beside the application.")
            return None
        return items

    def preview_pdf(self):
        items=self._validate_for_pdf()
        if not items:
            return
        try:
            import tempfile
            self.preview_path=os.path.join(tempfile.gettempdir(),"Advita_Quotation_Preview.pdf")
            self._make_pdf(self.preview_path,items)
            if os.name=="nt":
                os.startfile(self.preview_path)
            else:
                import subprocess
                subprocess.Popen(["xdg-open",self.preview_path])
            self.print_btn.config(state="normal")
            messagebox.showinfo("Preview opened","The quotation PDF has been opened in your default PDF viewer. Review it carefully. When ready, return here and click Print quotation.")
        except Exception as e:
            messagebox.showerror("Preview error",f"Could not open the quotation preview:\\n{e}")

    def print_pdf(self):
        path=getattr(self,"preview_path",None)
        if not path or not os.path.exists(path):
            messagebox.showwarning("Preview first","Please preview the quotation before printing.")
            return
        if not messagebox.askyesno("Confirm printing",
            "Have you reviewed the quotation preview?\\n\\nClick Yes to send it to your default printer."):
            return
        try:
            if os.name=="nt":
                os.startfile(path,"print")
                messagebox.showinfo("Print requested","The quotation was sent to the default PDF print handler. If it does not print automatically, use Ctrl+P in your PDF viewer.")
            else:
                import subprocess
                subprocess.Popen(["lp",path])
                messagebox.showinfo("Print requested","The quotation was sent to the system print queue.")
        except Exception as e:
            messagebox.showerror("Print error",f"Automatic printing failed. Open the preview PDF and press Ctrl+P.\\n\\n{e}")

    def export_pdf(self):
        items=self._validate_for_pdf()
        if not items:
            return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF document","*.pdf")],initialfile="Advita_Quotation.pdf")
        if not path:return
        try:
            self._make_pdf(path,items)
            self.preview_path=path
            self.print_btn.config(state="normal")
            messagebox.showinfo("PDF created",f"Quotation exported successfully:\\n{path}\\n\\nYou can now preview it or click Print quotation.")
        except Exception as e:
            messagebox.showerror("PDF error",f"Could not create PDF:\\n{e}")

    def _make_pdf(self,path,items):
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from PIL import Image
        data=self.quotation_data(); f=data["fields"]
        im=Image.open(TEMPLATE); iw,ih=im.size
        # Preserve the supplied artwork exactly; draw customer data and line items over blank areas.
        c=canvas.Canvas(path,pagesize=(iw,ih))
        c.drawImage(ImageReader(im),0,0,width=iw,height=ih)
        def y(top): return ih-top
        def txt(x,top,s,size=15,bold=False,color="#092754",maxw=None):
            s=str(s or "")
            c.setFillColor(color); c.setFont("Helvetica-Bold" if bold else "Helvetica",size)
            if maxw and c.stringWidth(s,"Helvetica-Bold" if bold else "Helvetica",size)>maxw:
                while s and c.stringWidth(s+"…","Helvetica-Bold" if bold else "Helvetica",size)>maxw: s=s[:-1]
                s += "…"
            c.drawString(x,y(top),s)
        # Customer details in the template's blank lines
        txt(215,380,f.get("to",""),13,maxw=400)
        txt(215,413,f.get("customer",""),13,maxw=400)
        address=f.get("address","").replace("\\n"," ")
        txt(215,447,address,12,maxw=405)
        txt(215,480,"",12)
        txt(215,539,f.get("phone",""),13,maxw=400)
        txt(215,573,f.get("email",""),12,maxw=400)
        txt(825,394,f.get("quote_no","AE/QT/001"),12,maxw=150)
        txt(825,438,f.get("quote_date",""),12,maxw=150)
        txt(825,486,f.get("validity",""),12,maxw=150)
        # Item table rows: template coordinates in pixels from top
        row_top=654; row_h=41
        subtotal=0
        for i,item in enumerate(items[:10]):
            top=row_top+i*row_h+25
            desc=item["description"]
            txt(59,top,str(i+1),12)
            txt(110,top,desc,11,maxw=465)
            txt(615,top,money(item["quantity"]),11)
            txt(704,top,money(item["unit_price"]),11,maxw=120)
            amount=item["quantity"]*item["unit_price"]; subtotal+=amount
            txt(854,top,money(amount),11,maxw=130)
        try: gst_rate=max(0,float(f.get("gst","0") or 0))
        except ValueError: gst_rate=0
        tax=subtotal*gst_rate/100; total=subtotal+tax
        # Totals region at lower right
        txt(854,1090,money(subtotal),12,maxw=130)
        txt(854,1131,f"{gst_rate:g}%",12,maxw=130)
        txt(854,1175,money(total),12,True,"#092754",maxw=130)
        # Terms and signature fields; translated customer-facing fields are user-selected via Gemini.
        txt(220,1290,f.get("payment",""),11,maxw=300)
        txt(290,1324,f.get("delivery",""),11,maxw=300)
        validity=f.get("validity","15 days")
        txt(245,1358,validity,11,maxw=80)
        c.save()

if __name__=="__main__":
    root=tk.Tk()
    try:
        style=ttk.Style()
        if "vista" in style.theme_names(): style.theme_use("vista")
    except Exception: pass
    QuotationApp(root)
    root.mainloop()
