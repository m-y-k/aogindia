import re

file = r"d:\Drone Projects\AOG India\index.html"
with open(file, 'r', encoding='utf-8', errors='replace') as f:
    html = f.read()

# The hint dots ended up after </section> - move them inside
# Remove the misplaced hint after </section>
html = re.sub(
    r'(  </section>)\s*\n\s*<!-- Mobile swipe hint dots -->\s*\n\s*<div class="shub-scroll-hint"[^<]*(?:<span[^/]*/span>)+</div>',
    r'\1',
    html
)

# Now inject it inside the grid div, before the closing </div> of .services-hub-grid
# The grid is: <div class="services-hub-grid" ...> ... </div>
# followed by </div> (container) </section>
# We want to add hint AFTER the </div> that closes the grid, still inside .container
html = re.sub(
    r'(      </div>\n)\s*(    </div>\n  </section>\n\n  <!-- ========== CREATORS)',
    r'\1      <!-- Mobile swipe hint dots -->\n      <div class="shub-scroll-hint" aria-hidden="true"><span class="active"></span><span></span><span></span><span></span><span></span></div>\n\n\2',
    html
)

with open(file, 'w', encoding='utf-8', newline='') as f:
    f.write(html)
print("Done")
